#!/usr/bin/env python3
"""
PRISM Evidence Bundle Generator v1.1.0

Creates audit-ready evidence bundles for deliverables.
Includes hashes, manifests, validation results, and toolchain info.

Usage:
    python evidence_bundle.py --run-id UUID --deliverables model.xlsx memo.pdf
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class DeliverableInfo:
    """Information about a deliverable file."""
    filename: str
    path: str
    size_bytes: int
    sha256: str
    mime_type: str
    created: str


@dataclass
class ToolchainInfo:
    """Toolchain version information."""
    python_version: str
    libreoffice_version: str
    openpyxl_version: str
    reportlab_version: str
    node_version: str
    pptxgenjs_version: str
    prism_version: str


@dataclass
class EvidenceManifest:
    """Complete evidence manifest."""
    run_id: str
    timestamp: str
    prism_version: str
    
    deliverables: List[DeliverableInfo]
    toolchain: ToolchainInfo
    
    validation_summary: Dict
    
    bundle_hash: Optional[str] = None


class EvidenceBundleGenerator:
    """
    Generates evidence bundles for audit and compliance.
    
    Creates:
    - SHA-256 hashes of all deliverables
    - Toolchain version snapshot
    - Validation result summary
    - Complete manifest
    """
    
    PRISM_VERSION = "1.1.0"
    
    MIME_TYPES = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pdf': 'application/pdf',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.json': 'application/json',
        '.md': 'text/markdown',
        '.txt': 'text/plain',
        '.csv': 'text/csv'
    }
    
    def __init__(self, run_id: str, output_dir: str = "/evidence"):
        """
        Initialize evidence bundle generator.
        
        Args:
            run_id: Unique run identifier
            output_dir: Base output directory
        """
        self.run_id = run_id
        self.output_dir = Path(output_dir) / run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate(
        self,
        deliverable_paths: List[str],
        recalc_result: Optional[Dict] = None,
        validation_result: Optional[Dict] = None,
        cell_ledger: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate complete evidence bundle.
        
        Args:
            deliverable_paths: Paths to deliverable files
            recalc_result: Result from recalc_v2.py
            validation_result: Result from model_validator.py
            cell_ledger: Cell creation audit trail
            
        Returns:
            Path to manifest.json
        """
        
        # Create subdirectories
        (self.output_dir / "deliverables").mkdir(exist_ok=True)
        (self.output_dir / "validation").mkdir(exist_ok=True)
        (self.output_dir / "ledger").mkdir(exist_ok=True)
        (self.output_dir / "toolchain").mkdir(exist_ok=True)
        
        # Process deliverables
        deliverables = []
        for path in deliverable_paths:
            if Path(path).exists():
                info = self._process_deliverable(path)
                deliverables.append(info)
            else:
                print(f"Warning: Deliverable not found: {path}", file=sys.stderr)
        
        # Collect toolchain info
        toolchain = self._collect_toolchain_info()
        
        # Save validation results
        if recalc_result:
            with open(self.output_dir / "validation" / "recalc_result.json", "w") as f:
                json.dump(recalc_result, f, indent=2)
        
        if validation_result:
            with open(self.output_dir / "validation" / "validation_result.json", "w") as f:
                json.dump(validation_result, f, indent=2)
        
        # Save ledger
        if cell_ledger:
            with open(self.output_dir / "ledger" / "cell_ledger.json", "w") as f:
                json.dump(cell_ledger, f, indent=2)
        
        # Save toolchain
        with open(self.output_dir / "toolchain" / "versions.json", "w") as f:
            json.dump(asdict(toolchain), f, indent=2)
        
        # Create validation summary
        validation_summary = self._create_validation_summary(recalc_result, validation_result)
        
        # Create manifest
        manifest = EvidenceManifest(
            run_id=self.run_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            prism_version=self.PRISM_VERSION,
            deliverables=deliverables,
            toolchain=toolchain,
            validation_summary=validation_summary
        )
        
        # Save manifest (first pass)
        manifest_path = self.output_dir / "manifest.json"
        manifest_dict = {
            'run_id': manifest.run_id,
            'timestamp': manifest.timestamp,
            'prism_version': manifest.prism_version,
            'deliverables': [asdict(d) for d in deliverables],
            'toolchain': asdict(toolchain),
            'validation_summary': validation_summary,
            'bundle_hash': None
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest_dict, f, indent=2)
        
        # Calculate bundle hash
        bundle_hash = self._calculate_bundle_hash()
        manifest_dict['bundle_hash'] = bundle_hash
        
        # Save manifest (final)
        with open(manifest_path, "w") as f:
            json.dump(manifest_dict, f, indent=2)
        
        return str(manifest_path)
    
    def _process_deliverable(self, path: str) -> DeliverableInfo:
        """Process a deliverable file."""
        
        path = Path(path)
        
        # Copy to bundle
        dest = self.output_dir / "deliverables" / path.name
        shutil.copy2(path, dest)
        
        # Calculate hash
        sha256 = self._calculate_file_hash(path)
        
        # Determine MIME type
        mime_type = self.MIME_TYPES.get(path.suffix.lower(), 'application/octet-stream')
        
        return DeliverableInfo(
            filename=path.name,
            path=str(dest),
            size_bytes=path.stat().st_size,
            sha256=sha256,
            mime_type=mime_type,
            created=datetime.utcnow().isoformat() + "Z"
        )
    
    def _calculate_file_hash(self, path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _collect_toolchain_info(self) -> ToolchainInfo:
        """Collect version information for all tools."""
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # LibreOffice version
        try:
            result = subprocess.run(["soffice", "--version"], capture_output=True, text=True, timeout=10)
            lo_version = result.stdout.strip()
        except:
            lo_version = "Unknown"
        
        # Python packages
        try:
            import openpyxl
            openpyxl_version = openpyxl.__version__
        except:
            openpyxl_version = "Not installed"
        
        try:
            import reportlab
            reportlab_version = reportlab.Version
        except:
            reportlab_version = "Not installed"
        
        # Node version
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
            node_version = result.stdout.strip()
        except:
            node_version = "Not installed"
        
        # pptxgenjs version
        try:
            result = subprocess.run(
                ["node", "-e", "console.log(require('pptxgenjs').version)"],
                capture_output=True, text=True, timeout=10
            )
            pptxgenjs_version = result.stdout.strip() if result.returncode == 0 else "Not installed"
        except:
            pptxgenjs_version = "Not installed"
        
        return ToolchainInfo(
            python_version=python_version,
            libreoffice_version=lo_version,
            openpyxl_version=openpyxl_version,
            reportlab_version=reportlab_version,
            node_version=node_version,
            pptxgenjs_version=pptxgenjs_version,
            prism_version=self.PRISM_VERSION
        )
    
    def _create_validation_summary(
        self,
        recalc_result: Optional[Dict],
        validation_result: Optional[Dict]
    ) -> Dict:
        """Create validation summary."""
        
        summary = {
            'overall_status': 'UNKNOWN',
            'recalc_status': 'NOT_RUN',
            'validation_status': 'NOT_RUN',
            'cache_coverage': None,
            'error_count': 0,
            'warning_count': 0
        }
        
        if recalc_result:
            summary['recalc_status'] = 'PASS' if recalc_result.get('success') else 'FAIL'
            summary['cache_coverage'] = recalc_result.get('cache_coverage_percent')
        
        if validation_result:
            summary['validation_status'] = validation_result.get('status', 'UNKNOWN')
            summary['error_count'] = validation_result.get('error_count', 0)
            summary['warning_count'] = validation_result.get('warning_count', 0)
        
        # Determine overall status
        if summary['recalc_status'] == 'FAIL' or summary['validation_status'] == 'FAIL':
            summary['overall_status'] = 'FAIL'
        elif summary['validation_status'] == 'WARNING':
            summary['overall_status'] = 'WARNING'
        elif summary['recalc_status'] == 'PASS' and summary['validation_status'] == 'PASS':
            summary['overall_status'] = 'PASS'
        
        return summary
    
    def _calculate_bundle_hash(self) -> str:
        """Calculate hash of entire bundle."""
        
        sha256 = hashlib.sha256()
        
        for path in sorted(self.output_dir.rglob("*")):
            if path.is_file() and path.name != "manifest.json":
                sha256.update(path.name.encode())
                sha256.update(self._calculate_file_hash(path).encode())
        
        return sha256.hexdigest()


def generate_evidence_bundle(
    run_id: str,
    deliverables: List[str],
    recalc_result: Optional[Dict] = None,
    validation_result: Optional[Dict] = None,
    cell_ledger: Optional[List[Dict]] = None,
    output_dir: str = "/evidence"
) -> Dict:
    """
    Convenience function for evidence generation.
    
    Args:
        run_id: Unique run identifier
        deliverables: List of deliverable file paths
        recalc_result: Recalculation result dict
        validation_result: Validation result dict
        cell_ledger: Cell creation ledger
        output_dir: Base output directory
    
    Returns:
        Dict with bundle path and manifest
    """
    generator = EvidenceBundleGenerator(run_id, output_dir)
    manifest_path = generator.generate(
        deliverables,
        recalc_result,
        validation_result,
        cell_ledger
    )
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    return {
        'bundle_path': str(generator.output_dir),
        'manifest_path': manifest_path,
        'manifest': manifest
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PRISM Evidence Bundle Generator v1.1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evidence_bundle.py --run-id abc123 --deliverables model.xlsx
  python evidence_bundle.py --run-id abc123 --deliverables model.xlsx memo.pdf --recalc recalc.json
        """
    )
    parser.add_argument("--run-id", required=True, help="Unique run identifier")
    parser.add_argument("--deliverables", nargs="+", required=True, help="Deliverable file paths")
    parser.add_argument("--recalc", help="Path to recalc result JSON")
    parser.add_argument("--validation", help="Path to validation result JSON")
    parser.add_argument("--output-dir", default="/evidence", help="Output directory")
    
    args = parser.parse_args()
    
    recalc_result = None
    if args.recalc:
        with open(args.recalc) as f:
            recalc_result = json.load(f)
    
    validation_result = None
    if args.validation:
        with open(args.validation) as f:
            validation_result = json.load(f)
    
    result = generate_evidence_bundle(
        args.run_id,
        args.deliverables,
        recalc_result,
        validation_result,
        output_dir=args.output_dir
    )
    
    print(json.dumps(result, indent=2))
