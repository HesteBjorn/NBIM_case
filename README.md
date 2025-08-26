# NBIM Case: LLM-Powered Dividend Reconciliation System

## How to run script:

Install packages:
`pip install -r requirements.txt`

Place Anthropic API key in a file named `.env` in the root directory with variable name `ANTHROPIC_API_KEY`. API key can be retrieved from https://console.anthropic.com/settings/keys


Run script:

` cd src`

`python main.py`

## Case Description

### Background
NBIM processes approximately **8,000 dividend events annually** across **9,000+ equity holdings**, requiring daily reconciliation between NBIM internal booking system and what the global custodian sends us. Manual processes are time-consuming and error-prone. We want to explore how Large Language Models could transform this workflow - from break detection to automated remediation.

### Your Challenge
Design and implement an **LLM-powered system** to reconcile the provided dividend data. How could LLM agents improve this process and be a dynamic system identifying issues?

## Technical Context

- **Budget**: $50 USD for LLM API usage (OpenAI or Anthropic), 1 month subscription fee will be reimbursed by NBIM
- **Models**: Use any model tier - focus on architecture over output quality
- **Data**: 
  - `NBIM_Dividend_Bookings.csv`
  - `CUSTODY_Dividend_Bookings.csv`
- **Cases**: 3 dividend events with varying complexity – these are the different `coac_event_keys` in the dataset

## Key Questions to Explore

- How can LLMs classify and prioritize reconciliation breaks?
- What types of intelligent agents could automate the entire workflow?
- What safeguards are needed for autonomous financial operations?

## Required Deliverables

### 1. Working Prototype
- LLM integration that processes the test data
- Classification and reconciliation logic
- Documentation of prompts and approach

### 2. Architecture Vision
- Design for an agent-based system

### 3. Analysis & Recommendations
- Innovative use cases you've identified
- Risk assessment and mitigation strategies

## Presentation (10 minutes)

Present your solution, focusing on:
- **Demo of your LLM system** – (On your local machine)
- Most innovative ideas for automation
- Practical next steps

## What We're Looking For

- **Creative thinking** about LLM applications in finance and ability to identify where LLMs add value
- **Practical solutions** to real operational challenges
- **Innovation in approach** rather than domain expertise of dividend reconciliation
- **Understanding** of both opportunities, challenges and risks

---

*This case focuses on exploring the potential of LLMs to transform financial operations through intelligent automation and reconciliation processes.*

