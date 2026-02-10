# ACOS v3.0 - Complete Beginner's Guide

Welcome! This guide is written for people with **zero programming experience**. If you've never written code before, you're in the right place.

---

## Table of Contents

1. [What is ACOS?](#what-is-acos)
2. [How Does It Work?](#how-does-it-work)
3. [Before You Start](#before-you-start)
4. [Getting Started Step-by-Step](#getting-started-step-by-step)
5. [The Vision Interview](#the-vision-interview)
6. [Understanding the Process](#understanding-the-process)
7. [What Happens Behind the Scenes](#what-happens-behind-the-scenes)
8. [Your Role as the User](#your-role-as-the-user)
9. [Common Questions](#common-questions)
10. [Troubleshooting](#troubleshooting)
11. [Glossary](#glossary)

---

## What is ACOS?

### In Simple Terms

ACOS is like having a **team of expert programmers** working for you, but they're AI agents. You tell them what you want to build, and they figure out how to build it.

Think of it like this:
- **You** = The client who knows what they want
- **ACOS** = A construction company that builds it for you

### What Can ACOS Build?

ACOS can help you build:
- Websites
- Web applications
- Mobile apps
- APIs (ways for apps to talk to each other)
- Databases
- And much more

### What Makes ACOS Special?

1. **You don't need to know how to code** - Just describe what you want
2. **It asks questions** - To make sure it understands you correctly
3. **It checks its own work** - Multiple reviewers verify everything
4. **It learns** - Gets smarter with every project
5. **It never forgets** - Everything is documented

---

## How Does It Work?

### The Simple Version

```
YOU: "I want a website where people can share recipes"
         ↓
ACOS: Asks you questions to understand exactly what you need
         ↓
ACOS: Breaks it down into small pieces
         ↓
ACOS: Builds each piece
         ↓
ACOS: Checks each piece for quality
         ↓
ACOS: Puts it all together
         ↓
YOU: Get your recipe website!
```

### The Team Behind ACOS

ACOS has different "agents" (think of them as team members):

| Team Member | What They Do |
|-------------|--------------|
| **The Architect** | The project manager - understands your vision and creates the plan |
| **The Developer** | The builder - writes the actual code |
| **QA Reviewer** | The quality checker - makes sure everything works |
| **Security Reviewer** | The security guard - makes sure it's safe |
| **Performance Reviewer** | The efficiency expert - makes sure it's fast |

---

## Before You Start

### What You Need

1. **A computer** (Mac, Windows, or Linux)
2. **Claude Code installed** - This is the AI assistant that runs ACOS
3. **A clear idea** of what you want to build (don't worry if it's vague - ACOS will help you clarify)

### What You DON'T Need

- Programming knowledge
- Technical vocabulary
- Design skills
- Database knowledge

ACOS will handle all the technical stuff.

---

## Getting Started Step-by-Step

### Step 1: Open Your Terminal

The terminal is a text-based way to interact with your computer. Don't worry - you'll only need to type a few simple commands.

**On Mac:**
1. Press `Command + Space` to open Spotlight
2. Type "Terminal"
3. Press Enter

**On Windows:**
1. Press `Windows key + R`
2. Type "cmd"
3. Press Enter

### Step 2: Navigate to Where You Want Your Project

Think of your computer as a filing cabinet. You need to tell the computer where to put your project.

Type this command (replace the path with where you want your project):

```bash
cd ~/Documents
```

> **What does this mean?**
> - `cd` = "change directory" (go to a folder)
> - `~/Documents` = Your Documents folder

### Step 3: Create a Folder for Your Project

```bash
mkdir my-project
cd my-project
```

> **What does this mean?**
> - `mkdir` = "make directory" (create a folder)
> - `my-project` = The name of your folder (you can change this)

### Step 4: Open Claude Code

You have two ways to open Claude Code with ACOS:

**Option A: Use the ACOS CLI** (recommended)

```bash
acos start
```

This always opens a **fresh new session**. ACOS context loads automatically.

**Option B: Open Claude Code directly**

```bash
claude
```

Then type `/acos-start` inside Claude Code to initialize your project.

> **Tip:** If you closed your terminal mid-project and want to pick up where you left off, use `acos resume` instead. This reopens your previous session with all the conversation history intact.

### Step 5: Start Your Vision

Once inside Claude Code, the `/acos-start` skill initializes your project structure (if needed) and begins the vision interview. The Architect greets you immediately. You're now ready for the most important part - telling The Architect what you want to build!

---

## The Vision Interview

This is where you describe your idea to The Architect. This is a **conversation**, not a form to fill out.

### How It Works

1. You describe your idea in plain English
2. The Architect asks you questions
3. You answer the questions
4. Repeat until The Architect understands your vision

### Example Conversation

**You:** "I want to build a website where people can share their favorite recipes."

**Architect:** "Great idea! Let me understand more. Who will use this website?"

**You:** "Mostly home cooks who want to share family recipes. Maybe some professional chefs too."

**Architect:** "Got it. What features do you absolutely need?"

**You:** "People should be able to post recipes with photos, search for recipes, and save their favorites."

**Architect:** "Should users create accounts, or can anyone post?"

**You:** "They need accounts. I don't want spam recipes."

*...and so on...*

### Topics The Architect Will Ask About

1. **Who will use it?** - Your target audience
2. **What devices?** - Phone, computer, tablet?
3. **Must-have features** - What's essential?
4. **Nice-to-have features** - What would be great but not essential?
5. **Look and feel** - What style do you want?
6. **How big?** - How many users do you expect?
7. **Any special requirements?** - Security, privacy, etc.

### Tips for a Good Interview

✅ **DO:**
- Describe what you want, not how to build it
- Use everyday language
- Give examples when possible
- Say "I don't know" if you're unsure
- Ask The Architect to explain if something is confusing

❌ **DON'T:**
- Worry about technical terms
- Rush through answers
- Assume ACOS knows what you mean
- Be afraid to change your mind

### When the Interview is Complete

When The Architect has enough information, it will create two important documents:

1. **Vision Interview** - The complete Q&A
2. **Vision Document** - A summary of your requirements

These become the "source of truth" - the reference for everything that follows.

### Ending the Interview

When you feel you've explained everything, or The Architect seems to have enough information, you can say:

> "That's enough" or "I think that covers it"

---

## Understanding the Process

### The Hierarchy

ACOS breaks your project into a hierarchy:

```
YOUR VISION
    │
    └── EPIC 1 (A major part of your project)
    │       │
    │       └── STORY 1.1 (A feature within that part)
    │       │       │
    │       │       └── SLICE 1.1.1 (A small piece of work)
    │       │       └── SLICE 1.1.2
    │       │
    │       └── STORY 1.2
    │
    └── EPIC 2
            └── ...
```

### Real Example

**Vision:** Recipe sharing website

**Epic 1:** User System
- **Story 1.1:** User Registration
  - *Slice 1.1.1:* Create signup form
  - *Slice 1.1.2:* Add password security
  - *Slice 1.1.3:* Send confirmation email
- **Story 1.2:** User Login
  - *Slice 1.2.1:* Create login form
  - *Slice 1.2.2:* Remember me feature

**Epic 2:** Recipe Management
- **Story 2.1:** Create Recipes
  - *Slice 2.1.1:* Recipe form
  - *Slice 2.1.2:* Photo upload
- **Story 2.2:** Search Recipes
  - ...

### Why This Matters to You

You don't need to create this breakdown - ACOS does it for you. But understanding it helps you:
- Know what's happening
- Provide better feedback
- Track progress

---

## What Happens Behind the Scenes

### For Each Slice

1. **Developer gets assignment** - The Architect tells the Developer what to build
2. **Developer builds it** - Code is written
3. **Developer creates evidence** - Proves the work is done
4. **Reviewers check it** - Multiple reviewers verify quality
5. **If problems found** - Goes back for fixes
6. **If approved** - Moves to the next slice

### The Review Process

Every piece of work is checked by reviewers:

| Reviewer | What They Check |
|----------|-----------------|
| QA Reviewer | Does it work correctly? Is it complete? |
| Security Reviewer | Is it safe? Can it be hacked? |
| Performance Reviewer | Is it fast? Will it slow down? |
| Integration Reviewer | Does it work with other parts? |

**Important:** Reviewers work independently. They can't see each other's feedback. This prevents bias and ensures thorough checking.

### When Things Get Rejected

If reviewers find problems, the work goes back for fixes. This is **normal and good** - it means the system is catching issues before they become problems.

The Architect receives all feedback and creates a plan to fix everything in one go.

---

## Your Role as the User

### What You Need to Do

1. **Describe your vision clearly** during the interview
2. **Answer questions** when The Architect asks
3. **Provide feedback** if something doesn't match your expectations
4. **Make decisions** when there are multiple options

### What You DON'T Need to Do

- Write code
- Understand technical details
- Manage the team
- Check the code quality (reviewers do this)

### Commands You Can Give

At any time, you can tell ACOS:

| Say This | What Happens |
|----------|--------------|
| "That's enough" | Ends the interview/questioning |
| "I changed my mind about..." | Updates your requirements |
| "Can you explain..." | Get clarification |
| "Show me the status" | See project progress |
| "I want to focus on X first" | Prioritize certain features |

### Resuming a Previous Session

If you close your terminal and want to continue where you left off:

```bash
acos resume
```

This reopens the last conversation you had in that project directory, with all the history and context preserved.

### Checking Progress

In Claude Code, type `/acos-status` to see how your project is going.

---

## Common Questions

### "How long will my project take?"

It depends on:
- How complex your vision is
- How many features you want
- Whether you need integrations with other services

ACOS doesn't give time estimates because every project is different.

### "What if I change my mind about something?"

That's fine! Just tell The Architect what you want to change. The plan will be updated.

**Note:** Changing things after work has started means some work might need to be redone.

### "What if I don't understand a question?"

Ask for clarification! Say something like:
- "Can you explain that in simpler terms?"
- "What do you mean by [term]?"
- "Can you give me an example?"

### "What if something goes wrong?"

ACOS has safeguards:
- Everything is saved and documented
- Reviewers catch problems
- The Architect can adjust plans
- You can always intervene

If something seems stuck, you can:
1. Check the status: type `/acos-status` in Claude Code
2. Ask what's happening
3. Provide guidance

### "Do I own what ACOS builds?"

Yes! Everything ACOS builds is yours. It's stored in your project folder.

### "Can I see what ACOS is doing?"

Yes! All decisions, reviews, and communications are saved in the `memory/` folder. You can look at any file to see what happened.

---

## Troubleshooting

### "I don't see ACOS skills in the menu"

Make sure you're running Claude Code from a directory that contains the `.claude/` folder with ACOS agents and skills. The CLAUDE.md file at the project root auto-loads at session start.

### "ACOS not initialized"

Type `/acos-start` in Claude Code — it will create the necessary directories automatically.

### "I'm confused about what's happening"

Type `/acos-status` in Claude Code to see the current state. If still confused, just ask: "What's the current status of my project?"

### "The interview is taking forever"

The Architect asks many questions to ensure it understands you correctly. This upfront investment saves time later by avoiding misunderstandings.

If you feel ready to move on, say "That's enough for now, let's start building."

### "I see error messages"

Don't panic! Copy the error message and paste it into Claude Code. Ask: "What does this error mean and how do I fix it?"

---

## Glossary

Here are common terms you might encounter:

| Term | Plain English Meaning |
|------|----------------------|
| **Agent** | An AI team member with a specific job |
| **API** | A way for programs to talk to each other |
| **Backend** | The behind-the-scenes part of an app (databases, servers) |
| **Database** | Where information is stored |
| **Endpoint** | A URL where your app can receive or send data |
| **Evidence Bundle** | Proof that work was completed |
| **Orchestration Skill** | A workflow that coordinates multiple agents in a sequence |
| **Frontend** | The part of an app you see and interact with |
| **Git** | A system for tracking changes to code |
| **Handoff** | When one agent passes work to another |
| **Initialize** | Set up for the first time (handled by `/acos-start`) |
| **Memory** | Where ACOS stores information about your project |
| **Path** | The location of a file or folder |
| **Repository** | A project folder tracked by Git |
| **Review** | When code is checked for quality |
| **Slice** | The smallest unit of work |
| **Source of Truth** | The authoritative document everyone references |
| **Terminal** | The text-based way to control your computer |
| **Vision** | Your complete project idea |

---

## Summary

1. **Start a session:** Run `acos start` (fresh) or `acos resume` (continue previous)
2. **Initialize:** Type `/acos-start` if not auto-prompted
3. **Describe:** Tell The Architect what you want to build
4. **Answer:** Respond to clarifying questions
5. **Wait:** ACOS builds and reviews each piece
6. **Provide feedback:** If something isn't right
7. **Get your project:** Fully built and tested

Remember:
- You don't need to understand code
- Questions are good - ask anytime
- The process has built-in quality checks
- Everything is documented

**You're ready to start building with ACOS!**

---

## Need More Help?

- Type `/` in Claude Code to see all available ACOS commands
- Check the `QUICK-START.md` for a shorter guide
- Look at `PRD.md` for technical details (if curious)
- Ask questions directly in Claude Code

---

*ACOS v3.0 - Building software made simple*
