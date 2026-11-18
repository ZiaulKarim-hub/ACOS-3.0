/**
 * sock-ask.ts — one synchronous round trip to the Nemesis daemon, for the CLI's generic
 * requests (S6 review, S7 authoring, S8 release). stdin: one JudgeRequest JSON. stdout: the
 * daemon's reply line. Exit 2 when the socket is absent or unreachable.
 */
import * as fs from "node:fs";
import * as net from "node:net";
import { SOCK } from "./judge";

const chunks: Buffer[] = [];
for await (const c of process.stdin) chunks.push(c as Buffer);
const req = Buffer.concat(chunks).toString("utf8").trim();
if (!req || !fs.existsSync(SOCK)) process.exit(2);
const sock = net.createConnection(SOCK);
let buf = "";
sock.on("connect", () => sock.write(req + "\n"));
sock.on("data", (d) => { buf += d.toString("utf8"); });
sock.on("end", () => { process.stdout.write((buf.trim().split("\n").pop() ?? "") + "\n"); process.exit(0); });
sock.on("error", () => process.exit(2));
