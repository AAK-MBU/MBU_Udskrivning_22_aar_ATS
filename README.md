# MBU Udskrivning 22 år – Process dashboard updater

---

## 🔍 Overview

This project defines a Python-based Automation Server (ATS) process developed for Aarhus Kommune’s MBU automation platform.
The robot automates the full “Udskrivning 22 år” workflow — a process that ensures citizens transitioning out of the municipal dental service at age 22 are handled correctly across systems.

The process dynamically determines which sub-flow to run based on command-line parameters, enabling reuse of the same codebase for multiple stages in the pipeline.

---

## ⚙️ Main Responsibilities
- Fetch citizens who have turned 22 today
- Check if the citizen has the correct aftale in Solteq Tand
- Check if faglig vurdering has been performed
- Verify if a formular besvarelse exists for the citizen
- Confirm that the desired private clinic exists in Solteq Tand
- Check whether the formular submission has been journalized
- Pass workitems between ATS queues to move citizens through the full workflow

---

## 🧠 How it works

1. The robot is started in ATS with a specific flag, e.g. --borger_fyldt_22, --aftale_oprettet_i_solteq, etc.
2. Based on this parameter, it runs the corresponding module from /processes/sub_processes/.
3. Each step validates its part of the process using data from Solteq Tand and the journalizing database.
4. Results are stored as workitems in ATS and passed to the next queue.
5. When all steps have been completed, the process finalizes and reports results via the Process Dashboard API.

---

## 🧩 Structure

- main.py – Entry point for all subflows
- helpers/ – Shared utilities for ATS API, configs, and queue management
- processes/ – Core logic for queue handling, item processing, and error management
- processes/sub_processes/ – Modules for each individual stage in the 22-år flow
