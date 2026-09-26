# 🤖 DevPilot — Autonomous AI Software Engineer

> An autonomous AI Software Engineer agent built with **Swytchcode**, orchestrating engineering workflows across **GitHub**, **Jira**, and **Slack** with a strict **Human Approval Gate**, regression testing, and an audit trail.

---

## 1. What DevPilot Does

DevPilot acts as a junior/mid-level autonomous software engineer working alongside your team:
- **Understands** natural language software engineering requests.
- **Investigates** issues in Jira and cross-references source code in GitHub repositories.
- **Formulates** precise root-cause diagnoses and step-by-step implementation plans.
- **Enforces a strict Human Approval Gate** before making any code modifications or creating branches.
- **Implements** fixes on dedicated branches, avoiding risky direct-to-main pushes.
- **Executes real automated regression tests** and refuses to report success unless tests actually pass.
- **Opens Pull Requests** with detailed summaries and Jira ticket backlinks.
- **Updates Jira** with test status and pull request references.
- **Notifies the team on Slack** with actionable execution summaries.

```text
UNDERSTAND → INVESTIGATE → REASON → PLAN → ASK FOR APPROVAL → IMPLEMENT → TEST → CREATE PR → UPDATE JIRA → NOTIFY SLACK
```

---

## 2. Architecture

```text
                               +-------------------------------------+
                               |      Web UI / Slack Interface       |
                               |    (Interactive Glassmorphism UI)   |
                               +------------------+------------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               |        DevPilot Agent Core          |
                               |  - Task State Machine (12 states)   |
                               |  - LLM & Reasoning Engine           |
                               |  - Human Approval Gate              |
                               |  - Automated Test Execution Engine  |
                               |  - Immutable Audit Trail Logger     |
                               +------------------+------------------+
                                                  |
                     +----------------------------+----------------------------+
                     |                            |                            |
                     v                            v                            v
               +-----------+                +-----------+                +-----------+
               |   Jira    |                |  GitHub   |                |   Slack   |
               |   Tools   |                |   Tools   |                |   Tools   |
               +-----+-----+                +-----+-----+                +-----+-----+
                     \                            |                            /
                      \                           |                           /
                       +--------------------------v--------------------------+
                       |              Swytchcode Kernel (swy exec)           |
                       |    Execution Authority • Auth • Audit • Policies    |
                       +--------------------------+--------------------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               |  Target Repos, Jira Issues, Slack   |
                               |      (e.g. ai-inference-service)    |
                               +-------------------------------------+
```

---

## 3. Swytchcode Integration

DevPilot uses **Swytchcode** (`swy`) as its external API execution authority:
- All external interactions run through clean tool abstractions:
  - **Jira:** `jira.api.issue.get`, `jira.api.issue.create`, `jira.issue.comments.create`, `jira.api.search.post`
  - **GitHub:** `github.repo.get3`, `github.search.code`, `github.repos.contents.get`, `github.pull.create`, `github.pull.get`
  - **Slack:** `slack.chat.postmessage.create`, `slack.search.message.list`, `slack.conversations.history.list`
- **Error Normalization (Spec Section 26):** Low-level HTTP 401/403/404/429 codes from Swytchcode are translated into developer-facing actionable guidance.
- **Sandbox Fallback:** Includes a zero-setup sandbox environment with realistic mocks (`AICV-1432`, `PR #218`, `#dev-alerts`), so reviewers can test the complete end-to-end flow immediately.
- **Zero-Secret Logging (Spec Section 18 & 19):** Tokens, passwords, and bearer headers are recursively sanitized and redacted from all audit entries.

---

## 4. Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | OpenAI API Key for LLM reasoning | *(optional; defaults to deterministic engine if blank)* |
| `SWYTCHCODE_API_KEY` | Swytchcode API Key from app.swytchcode.com | *(optional for sandbox)* |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `""` |
| `GITHUB_OWNER` | GitHub owner or organization | `acme-corp` |
| `GITHUB_REPO` | Target repository name | `ai-inference-service` |
| `JIRA_URL` | Jira Cloud instance URL | `https://acme-corp.atlassian.net` |
| `JIRA_USER` | Jira account email | `developer@acme.corp` |
| `JIRA_API_TOKEN` | Jira API Token | `""` |
| `SLACK_BOT_TOKEN` | Slack Bot OAuth Token (`xoxb-...`) | `""` |
| `SLACK_CHANNEL` | Target Slack notifications channel | `#dev-alerts` |
| `PORT` | Web server port | `8000` |

---

## 5. How to Run Locally

### Prerequisites
- Python 3.10+
- (Optional) Swytchcode CLI: `curl -fsSL https://raw.githubusercontent.com/swytchcodehq/swytchcode-cli/main/install.sh | bash`

### Step 1: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Run Automated Tests
Verify agent logic, Swytchcode tool mocks, and end-to-end approval workflows:
```bash
python3 -m unittest discover -s backend/tests
```

### Step 3: Start DevPilot Server
```bash
python3 -m uvicorn backend.app.server:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser to access the dashboard.

---

## 6. How to Configure GitHub

1. Generate a GitHub Personal Access Token (classic or fine-grained) with `repo` permissions.
2. In Swytchcode:
   ```bash
   swy auth add github
   ```
   Or set `GITHUB_TOKEN=ghp_...` in your `.env`.

---

## 7. How to Configure Jira

1. Generate an Atlassian API Token from [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens).
2. In Swytchcode:
   ```bash
   swy auth add jira
   ```
   Or set `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN` in `.env`.

---

## 8. How to Configure Slack

1. Create a Slack App in your workspace with `chat:write` and `search:read` scopes.
2. In Swytchcode:
   ```bash
   swy auth add slack
   ```
   Or set `SLACK_BOT_TOKEN=xoxb-...` and `SLACK_CHANNEL=#dev-alerts` in `.env`.

---

## 9. Example Commands (Spec Section 21)

DevPilot supports all 6 canonical commands specified in the build spec:

| # | Command | Expected Output |
| :--- | :--- | :--- |
| **1** | `Investigate AICV-1432 and tell me what is causing the issue.` | Jira → GitHub → Root cause diagnosis. |
| **2** | `Create an implementation plan for AICV-1432.` | Requirements → Affected files → Step-by-step plan (No code changes). |
| **3** | `Fix AICV-1432.` | Jira → GitHub → Plan → **Human Approval Gate** → Dedicated branch → Automated tests → PR → Jira comment → Slack notification. |
| **4** | `Why is PR #218 failing?` | PR checks → Changed files → CI error analysis (`AssertionError: 0 != 3`). |
| **5** | `Why is AICV-1432 blocked?` | Jira + GitHub CI + Slack discussions → Cross-system blocker synthesis. |
| **6** | `Give me today's engineering summary.` | Completed, In Progress, Blocked, Pull Requests, Key discussions. |
| **7** | `@DevPilot create a Jira ticket from this conversation.` | Extracts context → Creates Jira Bug ticket → Posts confirmation. |

---

## 10. Demo Flow: The AICV-1432 Walkthrough

The repository includes a realistic computer vision demo repository: [`ai-inference-service/`](file:///Users/abhishekgoel/Documents/swytchcode/ai-inference-service).

### Scenario:
In `ai-inference-service/inference/blur_detection.py`, a bug causes camera blur detection to trigger immediately on a single transient low-confidence frame rather than requiring 3 consecutive frames. Automated regression tests in `tests/test_blur_detection.py` fail.

### Step-by-Step Demo Execution:
1. Open the DevPilot UI at `http://localhost:8000`.
2. Click the quick demo button **`🚀 Fix AICV-1432`** (or type `Fix AICV-1432`).
3. Watch DevPilot:
   - Fetch Jira issue `AICV-1432`.
   - Inspect `ai-inference-service/inference/blur_detection.py`.
   - Formulate the root cause diagnosis and prepare the unified code diff.
4. **Human Approval Gate triggers**:
   - The UI displays the proposed branch (`feat/aicv-1432-consecutive-frame-blur`), affected files, and unified color-coded diff.
   - DevPilot pauses and waits for authorization.
5. Click **`✓ Approve & Execute Fix`**:
   - Code change is applied to the dedicated branch.
   - Automated tests run: `python3 -m unittest discover -s tests`.
   - All 5 tests **PASS**.
   - PR `#219` is created.
   - Jira ticket `AICV-1432` is updated with test outcomes.
   - Slack notification is posted to `#dev-alerts`.
6. Inspect the **Swytchcode Audit Trail** on the right sidebar to review every executed tool call.

*(To reset the demo to the buggy state at any time, run: `python3 scripts/reset_demo.py`)*

---

## 11. Security & Approval Model (Spec Section 18)

DevPilot implements non-negotiable guardrails:
- **Zero Direct-to-Main Pushes:** All modifications are committed to isolated feature branches.
- **Strict Approval Gate:** The agent cannot modify code or submit pull requests without explicit human approval.
- **Honest Test Validation:** DevPilot never claims tests passed without running them with a 0 exit code.
- **Audit Logging:** Every tool execution is recorded with sanitized arguments.
- **Credential Protection:** Secrets, passwords, API tokens, and authorization headers are never logged or stored.

---

## 12. Known Limitations

- **Complex Merge Conflicts:** Merge conflicts require developer intervention before DevPilot can re-apply fixes.
- **Non-Python Test Runners:** Currently configured out-of-the-box for `python3 -m unittest` and `pytest`; other language runtimes require specifying custom test commands.
- **Sandbox Mode:** In environments without live GitHub/Jira/Slack credentials, DevPilot runs in sandbox mode using mock responses.
