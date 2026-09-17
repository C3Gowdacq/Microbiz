"""
agents -- Standalone business intelligence agents for the Rossmann project.

Each agent is a pure-function module that takes structured inputs and returns
structured outputs, with no database or API dependencies. These modules will
be wired into the full MicroBizAI pipeline later.

Available agents:
  - sales_agent:     RF-based sales forecasting (single-day & multi-day)
  - inventory_agent: Inventory risk assessment & reorder recommendations
"""
