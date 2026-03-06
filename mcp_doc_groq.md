---
description: Connect AI applications to external systems using the Model Context Protocol (MCP) for standardized tool integrations.
title: Remote Tools and MCP - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Remote Tools and Model Context Protocol (MCP)

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open-source standard that enables AI applications to connect with external systems through a universal interface. Groq supports remote tool use via MCP servers, allowing you to simply point to an MCP server URL and the Groq API will start using its tools without you having to implement any tool logic yourself.

This doc begins with a high-level overview of MCP and how it works. If you're already familiar with MCP, you can skip to the [How to Use Remote MCP with Groq](#how-to-use-remote-mcp-with-groq) section.

## [What is MCP?](#what-is-mcp)

Think of MCP as **"USB-C for AI"** \- instead of building custom integrations for each service, you connect once to an MCP server and gain access to all its tools.

Traditional tool calling requires you to implement each tool yourself - you write the code, host the infrastructure, and maintain the integrations. MCP flips this model by letting **external servers** provide the tools, while you simply connect to them.

In the context of tool use, MCP servers feature two main RPC endpoints:

* `tools/list` \- Lists available tools from the MCP server
* `tools/call` \- Executes a tool with the given arguments

The MCP client (typically the application making requests to an LLM inference API like Groq; this could be your own application code or an LLM API client like ChatGPT or Claude Code) will first discover the available tools from the MCP server by making a request to the `tools/list` endpoint. The response will be a list of tools that the MCP server provides. These tools are then provided to the model at inference time, and any tools the model returns via its `tool_calls` parameter are then sent to the MCP server for execution using the `tools/call` endpoint.

MCP servers can be hosted locally (on your own machine or on the same server as your application) or remotely by you or a third party. Most servers are connected to via HTTP/SSE; local servers can be connected to via stdio.

Remote MCP on Groq is currently in beta. Please let us know your feedback in our [Community](https://community.groq.com).

## [How to Use Remote Tools via MCP with Groq](#how-to-use-remote-tools-via-mcp-with-groq)

Groq's Responses API supports **remote tool use via MCP servers** via HTTPS where Groq handles all orchestration. Instead of implementing the tool discovery and tool calling loop yourself, you can use Groq's Responses API to handle it for you.

With remote tool use, the Groq API will discover tools and pass them into the model at inference time. Any tool calls returned by the model are then sent to the MCP server for execution. Then the Groq API will parse the tool results and make another request to the model with the tool results. You don't implement anything - just provide the MCP server URL and authentication.

Your App → Makes request to Groq API with MCP server definitions
   ↓
Groq API → Discovers available tools from MCP server
         → Makes request to LLM with tool definitions
         ← Model returns tool_calls (or, if no tool calls are needed, 
           returns final response)
   ↓
Groq API → Parses tool call arguments
         → Makes request to MCP server with tool call arguments
         ← MCP server returns results
   ↓
Groq API → Makes another request to LLM with tool results
         ← Model returns more tool_calls (returns to step 3), or 
           returns final response
   ↓
Your App

**Note**: You can also integrate MCP servers into local tool calling loops, but typically you see lower latency with server-side tool calls via remote MCP.

## [When to Use MCP](#when-to-use-mcp)

MCP is ideal for:

* **Third-party services**: GitHub, Stripe, databases, Slack, etc.
* **Standardized integrations**: Use community-maintained MCP servers
* **Reducing maintenance**: Let others handle tool updates and hosting
* **Quick prototyping**: Connect to existing tools without implementation work
* **Enterprise systems**: Connect to internal MCP servers for company-wide tool access

## [When NOT to Use MCP](#when-not-to-use-mcp)

MCP may not be the best choice for:

* **Custom business logic**: If you need proprietary algorithms or calculations specific to your business, [local tool calling](https://console.groq.com/docs/tool-use/local-tool-calling) gives you more control
* **Latency-sensitive operations**: Adding an external server adds network overhead. For critical path operations, local tools or [built-in tools](https://console.groq.com/docs/tool-use/built-in-tools) may be faster
* **Complex authentication flows**: If your tools require intricate auth patterns beyond simple headers, local implementation offers more flexibility
* **Debugging and iteration**: During early development, local tools are easier to debug and iterate on than external servers
* **Offline requirements**: MCP requires network access to remote servers. Local tools work offline

**Alternative:** For local MCP servers (stdio-based), you would need to implement the orchestration yourself, similar to local tool calling. In that case, regular local function calling might be simpler.

## [Supported Models](#supported-models)

Remote MCP is available on all Groq models that support [tool use](https://console.groq.com/docs/tool-use/overview#supported-models):

| Model ID                                  | Model                                                                  |
| ----------------------------------------- | ---------------------------------------------------------------------- |
| openai/gpt-oss-20b                        | [GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b)                          |
| openai/gpt-oss-120b                       | [GPT-OSS 120B](https://console.groq.com/docs/model/openai/gpt-oss-120b)                        |
| qwen/qwen3-32b                            | [Qwen3 32B](https://console.groq.com/docs/model/qwen3-32b)                                     |
| moonshotai/kimi-k2-instruct-0905          | [Kimi K2 Instruct](https://console.groq.com/docs/model/moonshotai/kimi-k2-instruct-0905)       |
| meta-llama/llama-4-scout-17b-16e-instruct | [Llama 4 Scout](https://console.groq.com/docs/model/meta-llama/llama-4-scout-17b-16e-instruct) |
| llama-3.3-70b-versatile                   | [Llama 3.3 70B](https://console.groq.com/docs/model/llama-3.3-70b-versatile)                   |
| llama-3.1-8b-instant                      | [Llama 3.1 8B Instant](https://console.groq.com/docs/model/llama-3.1-8b-instant)               |

## [Why Use MCP with Groq?](#why-use-mcp-with-groq)

Groq's implementation of MCP provides significant advantages:

* **Drop-in compatibility**: Existing OpenAI + MCP integrations work with just an endpoint change
* **Superior performance**: Groq's fast inference makes multi-step MCP workflows feel snappy
* **Cost efficiency**: Run agentic MCP workflows more cost-effectively at scale
* **Built-in security**: Authentication headers are securely handled and redacted from logs

## [Getting Started with MCP](#getting-started-with-mcp)

MCP tools are added to your API request through the `tools` parameter. Each MCP tool specifies the server URL and authentication details.

### [MCP Tool Structure](#mcp-tool-structure)

JSON

```
{
  "tools": [
    {
      "type": "mcp",
      "server_label": "Huggingface",
      "server_url": "https://mcp.huggingface.co",
      "headers": {
        "Authorization": "Bearer <YOUR_HF_TOKEN>"
      },
      "server_description": "Search and access AI models from Hugging Face",
      "require_approval": "never",
      "allowed_tools": null
    }
  ]
}
```

Key fields:

* **server\_label**: A friendly name for the MCP server (used in responses)
* **server\_url**: The URL of the MCP server endpoint
* **headers**: Authentication headers (securely handled by Groq)
* **server\_description**: Helps the model understand when to use these tools
* **require\_approval**: Whether human approval is required for the tool call (e.g. "never", "always")
* **allowed\_tools**: Allows you to filter the tools that the model can use (e.g. \["tool1", "tool2"\])

### [Your First MCP Request](#your-first-mcp-request)

Here's a complete example using [Hugging Face's MCP server](https://huggingface.co/settings/mcp) to search for trending AI models:

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-120b",
  input: "What models are trending on Huggingface?",
  tools: [
    {
      type: "mcp",
      server_label: "Huggingface",
      server_url: "https://huggingface.co/mcp",
    }
  ]
});

console.log(response);
```

```
import openai
import os

client = openai.OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-120b",
    input="What models are trending on Huggingface?",
    tools=[
        {
            "type": "mcp",
            "server_label": "Huggingface",
            "server_url": "https://huggingface.co/mcp",
        }
    ]
)

print(response)
```

```
curl -X POST "https://api.groq.com/openai/v1/responses" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": "What models are trending on Huggingface?",
    "tools": [
      {
        "type": "mcp",
        "server_label": "Huggingface",
        "server_url": "https://huggingface.co/mcp"
      }
    ]
  }'
```

MCP Response Structure

When using MCP with the Responses API, you'll receive a structured response containing:

1. **Tool Discovery**: Lists available tools from the MCP server
2. **Reasoning**: Shows the model's decision-making process
3. **MCP Call**: The actual tool execution with results
4. **Final Message**: The synthesized answer using tool data

JSON

```
{
"id": "resp_01k59jhydefcd8wb7hbc460yav",
"object": "response",
"status": "completed",
"output": [
  {
    "type": "mcp_list_tools",
    "id": "mcpl_1720577121",
    "server_label": "Huggingface",
    "tools": [...] // Available tools from the MCP server
  },
  {
    "type": "reasoning", 
    "content": [
      {
        "type": "reasoning_text",
        "text": "User asks: 'What are the trending models on Huggingface?' Need to fetch trending models..."
      }
    ]
  },
  {
    "type": "mcp_call",
    "server_label": "Huggingface", 
    "name": "model_search",
    "arguments": "{\"limit\":10,\"sort\":\"trendingScore\"}",
    "output": "Showing first 10 models matching sorted by trendingScore..."
  },
  {
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "output_text", 
        "text": "Here are the top 10 trending models on Hugging Face..."
      }
    ]
  }
]
}
```

## [The Responses API: Purpose-Built for MCP](#the-responses-api-purposebuilt-for-mcp)

While MCP can work with the Chat Completions API, [Groq's Responses API](https://console.groq.com/docs/responses-api) is specifically designed for agentic workflows involving tools and multi-step interactions.

### [Why Responses API for MCP?](#why-responses-api-for-mcp)

**Action-Oriented Design**

* Tool discovery is a separate, labeled step
* Reasoning is exposed as its own output type
* Tool calls are clearly identified and structured
* Better handling of multi-step tool workflows

**Native MCP Support**

* Built from the ground up with MCP in mind
* Clearer separation between reasoning and action
* More reliable stateless operation
* Future approval mechanisms will integrate seamlessly

**Better Developer Experience**

* See exactly what tools the MCP server provides
* View the model's reasoning process
* Track each MCP call and its results
* Easier debugging and troubleshooting

For detailed information on configuring the Responses API with Groq, see our [Responses API documentation](https://console.groq.com/docs/responses-api). Groq's remote MCP support is fully compatible with [OpenAI's remote MCP API](https://platform.openai.com/docs/guides/tools-connectors-mcp).

MCP servers have access to all data in your AI model's context, including your messages, system prompts, and previous conversation history. Only connect to MCP servers from trusted sources that you control or verify. Malicious servers could potentially exfiltrate sensitive information from your requests. Always review the server's documentation and security practices before integration.

## [MCP Examples](#mcp-examples)

### [Web Scraping with Firecrawl](#web-scraping-with-firecrawl)

Connect to [Firecrawl's MCP server](https://docs.firecrawl.dev/mcp-server) for automated web scraping and data extraction. You'll need a [Firecrawl API key](https://firecrawl.dev/app/api-keys) to authenticate.

**Important Notes:**

* Use a **descriptive `server_description`** to help the AI model understand when to use these tools
* Firecrawl requires you to **provide a URL** in your request for it to browse and extract content from
* The API key should be included in the server URL as shown in the example

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-120b",
  input: [
    {
      type: "message",
      role: "user",
      content: "What are the production models on https://console.groq.com/docs/models?"
    }
  ],
  tools: [
    {
      type: "mcp",
      server_label: "firecrawl",
      server_description: "Web scraping and content extraction capabilities",
      server_url: "https://mcp.firecrawl.dev/<APIKEY>/v2/mcp",
      require_approval: "never"
    }
  ],
  stream: false
});

console.log(response);
```

```
import openai
import os

client = openai.OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-120b",
    input=[
        {
            "type": "message",
            "role": "user",
            "content": "What are the production models on https://console.groq.com/docs/models?"
        }
    ],
    tools=[
        {
            "type": "mcp",
            "server_label": "firecrawl",
            "server_description": "Web scraping and content extraction capabilities",
            "server_url": "https://mcp.firecrawl.dev/<APIKEY>/v2/mcp",
            "require_approval": "never"
        }
    ],
    stream=False
)

print(response)
```

```
curl -X POST "https://api.groq.com/openai/v1/responses" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": [
      {
        "type": "message",
        "role": "user",
        "content": "What are the production models on https://console.groq.com/docs/models?"
      }
    ],
    "tools": [
      {
        "type": "mcp",
        "server_label": "firecrawl",
        "server_description": "Web scraping and content extraction capabilities",
        "server_url": "https://mcp.firecrawl.dev/<APIKEY>/v2/mcp",
        "require_approval": "never"
      }
    ],
    "stream": false
  }'
```

Example Firecrawl Response

A typical Firecrawl MCP response includes tool discovery, reasoning, and web scraping execution:

JSON

```
{
"id": "resp_01k5sv3np4fydva2jd9zzknbdv",
"object": "response",
"status": "completed",
"output": [
  {
    "type": "mcp_list_tools",
    "server_label": "firecrawl",
    "tools": [
      {
        "name": "firecrawl_scrape",
        "description": "Scrape content from a single URL with advanced options..."
      },
      {
        "name": "firecrawl_map", 
        "description": "Map a website to discover all indexed URLs..."
      },
      {
        "name": "firecrawl_search",
        "description": "Search the web and extract content from results..."
      },
      {
        "name": "firecrawl_crawl",
        "description": "Crawl a website and extract content from all pages..."
      }
    ]
  },
  {
    "type": "reasoning",
    "content": [{
      "type": "reasoning_text", 
      "text": "User wants models info from console.groq.com/docs/models. Will use firecrawl_search..."
    }]
  },
  {
    "type": "mcp_call",
    "server_label": "firecrawl",
    "name": "firecrawl_search",
    "arguments": "{\"query\":\"Groq production models\",\"scrapeOptions\":{\"formats\":[\"markdown\"]}}",
    "output": "{\"web\":[{\"url\":\"https://console.groq.com/docs/models\",\"markdown\":\"# Production Models...\"}]}"
  },
  {
    "type": "message",
    "role": "assistant", 
    "content": [{
      "type": "output_text",
      "text": "Here are the production models listed on Groq's documentation..."
    }]
  }
]
}
```

### [Web Search with Parallel](#web-search-with-parallel)

Enable natural language web search for your AI agents with [Parallel's MCP server](https://docs.parallel.ai/features/remote-mcp). You'll need a [Parallel API key](https://platform.parallel.ai/settings?tab=api-keys).

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-120b",
  input: "What are the best models for agentic workflows on Groq? Search only on console.groq.com",
  tools: [
    {
      type: "mcp",
      server_label: "parallel_web_search",
      server_url: "https://mcp.parallel.ai/v1beta/search_mcp/",
      headers: {
        "x-api-key": "<PARALLEL_API_KEY>"
      },
      require_approval: "never"
    }
  ]
});

console.log(response);
```

```
import openai
import os

client = openai.OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-120b",
    input="What are the best models for agentic workflows on Groq? Search only on console.groq.com",
    tools=[
        {
            "type": "mcp",
            "server_label": "parallel_web_search",
            "server_url": "https://mcp.parallel.ai/v1beta/search_mcp/",
            "headers": {
                "x-api-key": "<PARALLEL_API_KEY>"
            },
            "require_approval": "never"
        }
    ]
)

print(response)
```

```
curl -X POST "https://api.groq.com/openai/v1/responses" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": "What are the best models for agentic workflows on Groq? Search only on console.groq.com",
    "tools": [
      {
        "type": "mcp",
        "server_label": "parallel_web_search",
        "server_url": "https://mcp.parallel.ai/v1beta/search_mcp/",
        "headers": {
          "x-api-key": "<PARALLEL_API_KEY>"
        },
        "require_approval": "never"
      }
    ]
  }'
```

Example Web Search Response

JSON

```
{
  "id": "resp_01k59pzd4bfe698awmye9cnd99",
  "object": "response",
  "status": "completed",
  "output": [
    {
      "type": "mcp_list_tools",
      "server_label": "parallel_web_search",
      "tools": [
        {
          "name": "web_search_preview",
          "description": "Perform web searches with various search types and domain filtering...",
          "input_schema": {
            "properties": {
              "objective": { "type": "string" },
              "search_queries": { "type": "array" },
              "search_type": { "enum": ["list", "targeted", "general", "single_page"] },
              "include_domains": { "type": "array" }
            }
          }
        }
      ]
    },
    {
      "type": "reasoning",
      "content": [{
        "type": "reasoning_text",
        "text": "Need to find best models for agentic workflows on Groq from console.groq.com..."
      }]
    },
    {
      "type": "mcp_call",
      "server_label": "parallel_web_search",
      "name": "web_search_preview",
      "arguments": "{\"include_domains\":[\"console.groq.com\"],\"objective\":\"Find best models for agentic workflows\",\"search_queries\":[\"Groq agentic models\"],\"search_type\":\"targeted\"}",
      "output": "[Results with relevant information from console.groq.com]"
    },
    {
      "type": "message",
      "role": "assistant",
      "content": [{
        "type": "output_text",
        "text": "Best Groq models for agentic workflows based on console.groq.com documentation..."
      }]
    }
  ]
}
```

### [Payment Processing with Stripe](#payment-processing-with-stripe)

Automate invoicing with [Stripe's MCP server](https://docs.stripe.com/mcp). You'll need a [Stripe API key](https://docs.stripe.com/mcp#bearer-token) with appropriate permissions.

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-120b",
  input: "Create an invoice for $100 for customer Groq Labs Testing using Stripe.",
  tools: [
    {
      type: "mcp",
      server_label: "Stripe",
      server_url: "https://mcp.stripe.com",
      headers: {
        Authorization: "Bearer <STRIPE_TOKEN>"
      },
      require_approval: "never"
    }
  ]
});

console.log(response);
```

```
import openai
import os

client = openai.OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-120b",
    input="Create an invoice for $100 for customer Groq Labs Testing using Stripe.",
    tools=[
        {
            "type": "mcp",
            "server_label": "Stripe",
            "server_url": "https://mcp.stripe.com",
            "headers": {
                "Authorization": "Bearer <STRIPE_TOKEN>"
            },
            "require_approval": "never"
        }
    ]
)

print(response)
```

```
curl -X POST "https://api.groq.com/openai/v1/responses" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": "Create an invoice for $100 for customer Groq Labs Testing using Stripe.",
    "tools": [
      {
        "type": "mcp",
        "server_label": "Stripe",
        "server_url": "https://mcp.stripe.com",
        "headers": {
          "Authorization": "Bearer <STRIPE_TOKEN>"
        },
        "require_approval": "never"
      }
    ]
  }'
```

Example Stripe Multi-Step Workflow

MCP orchestrates multiple Stripe API calls to complete complex workflows. Here the model creates a customer, product, price, invoice, and finalizes it - all autonomously:

JSON

```
{
"id": "resp_01k59tasz2eg4as5q4n37kaqch",
"object": "response",
"status": "completed",
"output": [
  {
    "type": "mcp_list_tools",
    "server_label": "Stripe",
    "tools": [
      { "name": "create_customer" },
      { "name": "create_product" },
      { "name": "create_price" },
      { "name": "create_invoice" },
      { "name": "create_invoice_item" },
      { "name": "finalize_invoice" }
    ]
  },
  {
    "type": "reasoning",
    "content": [{
      "text": "Need to create $100 invoice for Groq Labs Testing. Steps: 1. Create customer 2. Create product/price 3. Create invoice 4. Add item 5. Finalize..."
    }]
  },
  { "type": "mcp_call", "name": "create_customer", "output": "{\"id\":\"cus_ABC\"}" },
  { "type": "mcp_call", "name": "create_product", "output": "{\"id\":\"prod_XYZ\"}" },
  { "type": "mcp_call", "name": "create_price", "output": "{\"id\":\"price_123\"}" },
  { "type": "mcp_call", "name": "create_invoice", "output": "{\"id\":\"in_456\"}" },
  { "type": "mcp_call", "name": "create_invoice_item" },
  { "type": "mcp_call", "name": "finalize_invoice", "output": "{\"status\":\"open\",\"url\":\"https://invoice.stripe.com/...\"}" },
  {
    "type": "message",
    "content": [{
      "text": "Invoice created and finalized for $100 USD for Groq Labs Testing..."
    }]
  }
]
}
```

This demonstrates MCP's power for **multi-step agentic workflows** \- the model autonomously determines the sequence of operations needed and executes them.

Other payment processors also support MCP, such as [PayPal's MCP server](https://www.paypal.ai/docs/tools/mcp-quickstart#remote-mcp-server).

## [Advanced Features](#advanced-features)

### [Multiple MCP Servers](#multiple-mcp-servers)

Connect to multiple MCP servers in a single request, allowing AI to coordinate across different systems:

JSON

```
{
  "tools": [
    {
      "type": "mcp",
      "server_label": "parallel_web_search",
      "server_url": "https://mcp.parallel.ai/<token>",
      "headers": { "x-api-key": "<PARALLEL_API_KEY>" },
      "server_description": "Search the web for real-time information"
    },
    {
      "type": "mcp",
      "server_label": "Stripe",
      "server_url": "https://mcp.stripe.com",
      "headers": { "Authorization": "Bearer <STRIPE_TOKEN>" },
      "server_description": "Create invoices and manage payments"
    },
    {
      "type": "mcp",
      "server_label": "github",
      "server_url": "https://mcp.github.com/v1",
      "headers": { "Authorization": "Bearer <GITHUB_TOKEN>" },
      "server_description": "Access GitHub repositories and create issues"
    }
  ]
}
```

The model will intelligently select which MCP server(s) to use based on the query.

### [Authentication & Security](#authentication--security)

MCP servers often require authentication. Groq handles credentials securely:

* **Headers sent only to MCP servers**: Tokens are only transmitted to the specific server URL
* **Redacted from logs**: Authentication headers are automatically redacted from Groq logs
* **HTTPS required**: All MCP server connections must use HTTPS

**Best Practices:**

* Use environment variables for API keys, never hardcode them
* Rotate credentials regularly
* Use the minimum required permissions for each MCP server
* Only connect to trusted MCP servers

### [Server Descriptions](#server-descriptions)

Provide clear `server_description` fields to help the model understand when to use each MCP server:

**❌ Bad:**

JSON

```
{
  "server_label": "stripe",
  "server_description": "Stripe API"
}
```

**✅ Good:**

JSON

```
{
  "server_label": "stripe",
  "server_description": "Use this to create invoices, process payments, manage subscriptions, and handle billing for customers. Can create customers, products, prices, and finalize invoices."
}
```

## [Troubleshooting](#troubleshooting)

### [Connection Errors](#connection-errors)

If you receive a `424 Failed Dependency` error:

JSON

```
{
  "error": {
    "message": "Error retrieving tool list from MCP server: 'Stripe' Http status code: 401 (Unauthorized)",
    "type": "external_connector_error",
    "param": "tools",
    "code": "http_error"
  }
}
```

Common causes:

* **Incorrect credentials**: Check your API keys and authentication headers
* **Invalid server URL**: Verify the MCP server endpoint is correct
* **Server unavailable**: The MCP server may be down or rate limiting

**Debugging steps:**

1. Verify credentials are correct and not expired
2. Test the MCP server URL directly (curl/Postman)
3. Check the MCP server's status page
4. Ensure you're using the correct authentication method
5. Try with a known working MCP server to isolate the issue

### [Model Not Using MCP Tools](#model-not-using-mcp-tools)

If the model isn't using your MCP tools:

1. **Add clear server descriptions** \- Help the model understand when to use each tool
2. **Be explicit in prompts** \- "Use the Stripe MCP server to create an invoice..."
3. **Check tool availability** \- Verify the MCP server returned tools in `mcp_list_tools`
4. **Use system prompts** \- Guide the model with instructions about when to use MCP

### [Approvals Flow](#approvals-flow)

If `require_approval` is set to "always", the Groq API will wait for human approval before executing the tool call.

If this is the case, Groq returns the following response:

JSON

```
{
  "type": "mcp_approval_request",
  "id": "req_12345",
  "server_label": "github",
  "name": "create_issue",
  "arguments": "{\"title\":\"Bug fix\"}"
}
```

You can then approve or reject the tool call by passing an `mcp_approval_response` in your next request to the Groq API.

JSON

```
{
  "type": "mcp_approval_response",
  "approval_request_id": "req_12345",
  "approve": true
}
```

You can also set `require_approval` to "never", which will cause the model to execute the tool call without human approval. This is the default behavior if `require_approval` is not set.

## [OpenAI Compatibility](#openai-compatibility)

Groq's MCP implementation is fully compatible with [OpenAI's remote MCP specification](https://platform.openai.com/docs/guides/tools-connectors-mcp). Existing integrations typically only need to change:

* **Base URL**: `https://api.openai.com/v1` → `https://api.groq.com/openai/v1`
* **Model name**: To a [Groq-supported model](https://console.groq.com/docs/models) like `openai/gpt-oss-120b`
* **API key**: To your [Groq API key](https://console.groq.com/keys)

## [Using MCP with Chat Completions API](#using-mcp-with-chat-completions-api)

While we recommend the Responses API for MCP, you can also use it with the Chat Completions API:

The Chat Completions API retrofits MCP onto a conversation-based interface. For the best MCP experience with multi-step workflows, use the Responses API.

Python

```
import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

const completion = await groq.chat.completions.create({
  model: "openai/gpt-oss-120b",
  messages: [
    {
      role: "user",
      content: "What models are trending on Huggingface?"
    }
  ],
  tools: [
    {
      type: "mcp",
      server_label: "Huggingface",
      server_url: "https://huggingface.co/mcp"
    }
  ]
});

console.log(completion.choices[0].message);
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "What models are trending on Huggingface?"
        }
    ],
    tools=[
        {
            "type": "mcp",
            "server_label": "Huggingface",
            "server_url": "https://huggingface.co/mcp"
        }
    ]
)

print(completion.choices[0].message)
```

```
curl -X POST "https://api.groq.com/openai/v1/chat/completions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {
        "role": "user",
        "content": "What models are trending on Huggingface?"
      }
    ],
    "tools": [
      {
        "type": "mcp",
        "server_label": "Huggingface",
        "server_url": "https://huggingface.co/mcp"
      }
    ]
  }'
```

## [Finding MCP Servers](#finding-mcp-servers)

Several organizations provide public MCP servers:

* **[MCP Servers Repository](https://github.com/modelcontextprotocol/servers)** \- Official collection of MCP servers
* **[Hugging Face MCP](https://huggingface.co/settings/mcp)** \- Access AI models and datasets
* **[Stripe MCP](https://docs.stripe.com/mcp)** \- Payment processing
* **[Firecrawl MCP](https://docs.firecrawl.dev/mcp-server)** \- Web scraping
* **[Parallel MCP](https://docs.parallel.ai/features/remote-mcp)** \- Web search
* **[PayPal MCP](https://www.paypal.ai/docs/tools/mcp-quickstart)** \- Payment processing

You can also build your own MCP server using the [MCP specification](https://modelcontextprotocol.io/specification/latest).

## [Next Steps](#next-steps)

* **[Explore Connectors](https://console.groq.com/docs/tool-use/remote-mcp/connectors)** \- Learn more about pre-built integrations for popular business applications
* **[Groq Built-In Tools](https://console.groq.com/docs/tool-use/built-in-tools)** \- Use web search and code execution without any setup
* **[Local Tool Calling](https://console.groq.com/docs/tool-use/local-tool-calling)** \- Define and execute custom tools in your application code
* **[Responses API](https://console.groq.com/docs/responses-api)** \- Deep dive into the API built for agentic workflows
* **[MCP Specification](https://spec.modelcontextprotocol.io/)** \- Build your own MCP servers