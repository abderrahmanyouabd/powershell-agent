---
description: Learn how to implement custom tools that execute in your application code for complete control over tool behavior.
title: Local Tool Calling - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Local Tool Calling

Local tool (function) calling gives you complete control over tool execution by defining and implementing functions in your application code. When the model needs to use a tool, it returns a structured request including the tool name and arguments; your code determines which function to call and parses the provided arguments, then you send the results back to the model for the final response. This gives you complete control but requires orchestration code.

The word "local" in local tool calling refers to the fact that the tool execution happens in your application code, rather than on Groq's servers. The functions you implement may connect to external resources such as databases, APIs, and external services, but they are "local" in the sense that they are executed on the same machine as the application code.

**Note on MCP:** Your local tools can also come from **local MCP servers** (via stdio) - they provide the tool definitions and implementations, but **your code is still responsible for orchestrating the calls**. This is different from [Remote MCP](https://console.groq.com/docs/tool-use/remote-mcp) where Groq's infrastructure handles the entire orchestration. If you want to use MCP tools with local orchestration, this pattern still applies.

## [How Local Tool Calling Works](#how-local-tool-calling-works)

With local tool calling, **execution happens in your code**. You control the environment, security, and implementation. You orchestrate the entire loop.

Your App → Makes request to Groq API with tool definitions   
   ↓ 
Groq API → Makes request to LLM model with user-provided tool definitions
         ← Model returns tool_calls (or, if no tool calls are needed, 
           returns final response)
   ↓
Your App → Parses tool call arguments
         → Executes function locally with provided arguments
         ← Function returns results
         → Makes request to Groq API with tool results 
   ↓
Groq API → Makes another request to LLM with tool results
         ← Model returns more tool_calls (returns to step 3), or 
           returns final response
   ↓
Your App

This pattern is ideal for:

* **Custom business logic** \- Implement proprietary workflows and calculations
* **Internal systems** \- Access your databases, APIs, and services
* **Security-sensitive operations** \- Control exactly how and when tools execute
* **Complex orchestration** \- Coordinate multiple internal systems

## [The Three Components of Local Tool Calling](#the-three-components-of-local-tool-calling)

To implement local tool calling, you need to provide three components:

### [1\. Tool Schema (Definition)](#1-tool-schema-definition)

A JSON schema that describes your tool to the model - what it does, what parameters it accepts, and when to use it. This is what the model "sees" and uses to decide whether to call your tool.

JSON

```
{
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "Evaluate a mathematical expression",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "The mathematical expression to evaluate"
        }
      },
      "required": ["expression"]
    }
  }
}
```

**Tips for better tool definitions:**

* **Clear descriptions**: The model uses your `description` field to decide when to use the tool, so make it clear and concise
* **Detailed parameter descriptions**: Help the model provide correct arguments by describing what each parameter expects

### [2\. Tool Implementation (Function)](#2-tool-implementation-function)

The actual function code that executes when the model calls your tool. Use a function map to connect tool names to implementations, and create a helper function to parse and execute tool calls:

Python

```
import json

def calculate(expression: str) -> str:
    """Execute the calculation"""
    try:
        result = eval(expression)  # Use safe evaluation in production
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# Map function names to implementations
available_functions = {
    "calculate": calculate,
    # Add more tools here as you build them
    # "get_weather": get_weather,
    # "search_database": search_database,
}

def execute_tool_call(tool_call):
    """Parse and execute a single tool call"""
    function_name = tool_call.function.name
    function_to_call = available_functions[function_name]
    function_args = json.loads(tool_call.function.arguments)
    
    # Call the function with unpacked arguments
    return function_to_call(**function_args)
```

```
function calculate(expression) {
  /**
   * Execute the calculation
   */
  try {
    const result = eval(expression); // Use safe evaluation in production
    return String(result);
  } catch (e) {
    return `Error: ${e.message}`;
  }
}

// Map function names to implementations
const availableFunctions = {
  calculate: calculate,
  // Add more tools here as you build them
  // get_weather: getWeather,
  // search_database: searchDatabase,
};

function executeToolCall(toolCall) {
  /**
   * Parse and execute a single tool call
   */
  const functionName = toolCall.function.name;
  const functionToCall = availableFunctions[functionName];
  const functionArgs = JSON.parse(toolCall.function.arguments);

  // Call the function with unpacked arguments
  return functionToCall(functionArgs.expression);
}

export { calculate, availableFunctions, executeToolCall };
```

### [3\. Orchestration (The Loop)](#3-orchestration-the-loop)

Code that ties it all together by following these steps:

1. Call the model with your tool schema
2. Check if the model returned tool calls
3. Execute your tool implementation with the provided arguments
4. Send results back to the model
5. Get the final response

Python

```
from groq import Groq

client = Groq()

# 1. Call model with tool schema
messages = [{"role": "user", "content": "What is 25 * 4?"}]

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
    tools=[calculate_tool_schema]  # Your schema from step 1
)

messages.append(response.choices[0].message)

# 2. Check for tool calls
if response.choices[0].message.tool_calls:
    # 3. Execute each tool call (using the helper function from step 2)
    for tool_call in response.choices[0].message.tool_calls:
        function_response = execute_tool_call(tool_call)
        
        # Add tool result to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.function.name,
            "content": str(function_response)
        })
    
    # 4. Send results back and get final response
    final = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )
```

```
import Groq from "groq-sdk";

const client = new Groq();

// 1. Call model with tool schema
const messages = [{ role: "user", content: "What is 25 * 4?" }];

const response = await client.chat.completions.create({
  model: "openai/gpt-oss-120b",
  messages: messages,
  tools: [calculateToolSchema], // Your schema from step 1
});

messages.push(response.choices[0].message);

// 2. Check for tool calls
if (response.choices[0].message.tool_calls) {
  // 3. Execute each tool call (using the helper function from step 2)
  for (const toolCall of response.choices[0].message.tool_calls) {
    const functionResponse = executeToolCall(toolCall);

    // Add tool result to messages
    messages.push({
      role: "tool",
      tool_call_id: toolCall.id,
      name: toolCall.function.name,
      content: String(functionResponse),
    });
  }

  // 4. Send results back and get final response
  const final = await client.chat.completions.create({
    model: "openai/gpt-oss-120b",
    messages: messages,
  });
}
```

**You are responsible for all three components.** The model doesn't know how your tools work - it only sees the schema. You implement the logic and orchestrate the loop.

Note that this example shows a **single turn** of tool calling (one request to LLM → tool execution → final response from LLM). Real agentic systems wrap this in a loop, checking if the model's response to the first tool result contains additional `tool_calls` and continuing until the model returns a final answer (no more `tool_calls`) or reaches your pre-defined maximum number of iterations. See the [Multi-Tool Example with Agentic Loop](#complete-multitool-example-with-agentic-loop) section below for multi-turn agentic patterns.

### [What the Model Returns](#what-the-model-returns)

When the model decides to use a tool, it returns a response with `finish_reason: "tool_calls"` and a `tool_calls` array:

JSON

```
{
  "model": "openai/gpt-oss-120b",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_d5wg",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"New York, NY\", \"unit\": \"fahrenheit\"}"
        }
      }]
    },
    "finish_reason": "tool_calls"
  }]
}
```

Key fields:

* `id` \- Unique identifier for this tool call (used when sending results back)
* `type` \- Always "function" for function calls
* `function.name` \- The name of the function to execute
* `function.arguments` \- JSON string of arguments to pass to the function

## [Complete Example: Calculator Tool](#complete-example-calculator-tool)

Here's a complete, runnable example with a calculator tool showing the full workflow in action:

Python

```
from groq import Groq
import json

# Initialize the Groq client
client = Groq()
MODEL = 'openai/gpt-oss-120b'

def calculate(expression):
    """Evaluate a mathematical expression"""
    try:
        result = eval(expression)  # Use safe evaluation in production
        return json.dumps({"result": result})
    except:
        return json.dumps({"error": "Invalid expression"})

def run_conversation(user_prompt):
    """Run a conversation with tool calling"""
    # Initialize the conversation
    messages = [
        {
            "role": "system",
            "content": "You are a calculator assistant. Use the calculate function to perform mathematical operations and provide the results."
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]
    
    # Define the tool schema
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Evaluate a mathematical expression",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate",
                        }
                    },
                    "required": ["expression"],
                },
            },
        }
    ]
    
    # Step 1: Make initial API call
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # Step 2: Check if the model wants to call tools
    if tool_calls:
        # Map function names to implementations
        available_functions = {
            "calculate": calculate,
        }
        
        # Add the assistant's response to conversation
        messages.append(response_message)
        
        # Step 3: Execute each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                expression=function_args.get("expression")
            )
            
            # Add tool response to conversation
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
        
        # Step 4: Get final response from model
        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        return second_response.choices[0].message.content
    
    # If no tool calls, return the direct response
    return response_message.content

# Example usage
user_prompt = "What is 25 * 4 + 10?"
print(run_conversation(user_prompt))
```

```
import Groq from "groq-sdk";

// Initialize the Groq client
const client = new Groq();
const MODEL = "openai/gpt-oss-120b";

function calculate(expression) {
  /**
   * Evaluate a mathematical expression
   */
  try {
    const result = eval(expression); // Use safe evaluation in production
    return JSON.stringify({ result: result });
  } catch (e) {
    return JSON.stringify({ error: "Invalid expression" });
  }
}

async function runConversation(userPrompt) {
  /**
   * Run a conversation with tool calling
   */
  // Initialize the conversation
  const messages = [
    {
      role: "system",
      content:
        "You are a calculator assistant. Use the calculate function to perform mathematical operations and provide the results.",
    },
    {
      role: "user",
      content: userPrompt,
    },
  ];

  // Define the tool schema
  const tools = [
    {
      type: "function",
      function: {
        name: "calculate",
        description: "Evaluate a mathematical expression",
        parameters: {
          type: "object",
          properties: {
            expression: {
              type: "string",
              description: "The mathematical expression to evaluate",
            },
          },
          required: ["expression"],
        },
      },
    },
  ];

  // Step 1: Make initial API call
  const response = await client.chat.completions.create({
    model: MODEL,
    messages: messages,
    tools: tools,
    tool_choice: "auto",
  });

  const responseMessage = response.choices[0].message;
  const toolCalls = responseMessage.tool_calls;

  // Step 2: Check if the model wants to call tools
  if (toolCalls) {
    // Map function names to implementations
    const availableFunctions = {
      calculate: calculate,
    };

    // Add the assistant's response to conversation
    messages.push(responseMessage);

    // Step 3: Execute each tool call
    for (const toolCall of toolCalls) {
      const functionName = toolCall.function.name;
      const functionToCall = availableFunctions[functionName];
      const functionArgs = JSON.parse(toolCall.function.arguments);
      const functionResponse = functionToCall(functionArgs.expression);

      // Add tool response to conversation
      messages.push({
        tool_call_id: toolCall.id,
        role: "tool",
        name: functionName,
        content: functionResponse,
      });
    }

    // Step 4: Get final response from model
    const secondResponse = await client.chat.completions.create({
      model: MODEL,
      messages: messages,
    });
    return secondResponse.choices[0].message.content;
  }

  // If no tool calls, return the direct response
  return responseMessage.content;
}

// Example usage
const userPrompt = "What is 25 * 4 + 10?";
runConversation(userPrompt).then((result) => console.log(result));
```

## [Parallel Tool Use](#parallel-tool-use)

Some models support **parallel tool use**, where multiple tools can be called simultaneously in a single request. For queries that require multiple tool calls, parallel tool use executes them simultaneously for better performance:

Python

```
import json
import os

from groq import Groq

# Initialize Groq client
client = Groq()
model = "openai/gpt-oss-120b"

# Define weather tools
def get_temperature(location: str):
    # This is a mock tool/function. In a real scenario, you would call a weather API.
    temperatures = {"New York": "22°C", "London": "18°C", "Tokyo": "26°C", "Sydney": "20°C"}
    return temperatures.get(location, "Temperature data not available")

def get_weather_condition(location: str):
    # This is a mock tool/function. In a real scenario, you would call a weather API.
    conditions = {"New York": "Sunny", "London": "Rainy", "Tokyo": "Cloudy", "Sydney": "Clear"}
    return conditions.get(location, "Weather condition data not available")

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_temperature",
            "description": "Get the temperature for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The name of the city",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_condition",
            "description": "Get the weather condition for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The name of the city",
                    }
                },
                "required": ["location"],
            },
        },
    }
]

# Make the initial request
def run_weather_assistant():
    # Define system messages for this request (fresh each time)
    messages = [
        {"role": "system", "content": "You are a helpful weather assistant."},
        {"role": "user", "content": "What's the weather and temperature like in New York and London? Respond with one sentence for each city. Use tools to get the current weather and temperature."},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=0.5,  # Keep temperature between 0.0 - 0.5 for best tool calling results
            tool_choice="auto",
            max_completion_tokens=4096,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls or []

        # Process tool calls
        messages.append(response_message)

        available_functions = {
            "get_temperature": get_temperature,
            "get_weather_condition": get_weather_condition,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)

            messages.append(
                {
                    "role": "tool",
                    "content": str(function_response),
                    "tool_call_id": tool_call.id,
                }
            )

        # Make the final request with tool call results
        final_response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=0.5,
            tool_choice="auto",
            max_completion_tokens=4096,
        )

        return final_response.choices[0].message.content
    except Exception as error:
        print("An error occurred:", error)
        raise error  # Re-raise the error so it can be caught by the caller

if __name__ == "__main__":
    result = run_weather_assistant()
    print("Final result:", result)
```

```
import Groq from "groq-sdk";

// Initialize Groq client
const groq = new Groq();
const model = "llama-3.3-70b-versatile";

// Define weather tools
function getTemperature(location) {
  // This is a mock tool/function. In a real scenario, you would call a weather API.
  const temperatures = {
    "New York": "22°C",
    London: "18°C",
    Tokyo: "26°C",
    Sydney: "20°C",
  };
  return temperatures[location] || "Temperature data not available";
}

function getWeatherCondition(location) {
  // This is a mock tool/function. In a real scenario, you would call a weather API.
  const conditions = {
    "New York": "Sunny",
    London: "Rainy",
    Tokyo: "Cloudy",
    Sydney: "Clear",
  };
  return conditions[location] || "Weather condition data not available";
}

// Define tools
const tools = [
  {
    type: "function",
    function: {
      name: "getTemperature",
      description: "Get the temperature for a given location",
      parameters: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "The name of the city",
          },
        },
        required: ["location"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "getWeatherCondition",
      description: "Get the weather condition for a given location",
      parameters: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "The name of the city",
          },
        },
        required: ["location"],
      },
    },
  },
];

// Make the initial request
export async function runWeatherAssistant() {
  // Define system messages for this request (fresh each time)
  const messages = [
    { role: "system", content: "You are a helpful weather assistant." },
    {
      role: "user",
      content:
        "What's the weather and temperature like in New York and London? Respond with one sentence for each city. Use tools to get the current weather and temperature.",
    },
  ];

  try {
    const response = await groq.chat.completions.create({
      model,
      messages,
      tools,
      temperature: 0.5, // Keep temperature between 0.0 - 0.5 for best tool calling results
      tool_choice: "auto",
      max_completion_tokens: 4096,
      parallel_tool_calls: true,
    });

    const responseMessage = response.choices[0].message;
    const toolCalls = responseMessage.tool_calls || [];

    // Process tool calls
    messages.push(responseMessage);

    const availableFunctions = {
      getTemperature,
      getWeatherCondition,
    };

    // Execute all tool calls in parallel using Promise.all
    const toolCallResults = await Promise.all(
      toolCalls.map(async (toolCall) => {
        const functionName = toolCall.function.name;
        const functionToCall = availableFunctions[functionName];
        const functionArgs = JSON.parse(toolCall.function.arguments);

        // Call corresponding tool function if it exists
        const functionResponse = functionToCall?.(functionArgs.location);

        return {
          role: "tool",
          content: functionResponse,
          tool_call_id: toolCall.id,
        };
      }),
    );

    // Add all tool results to messages
    messages.push(...toolCallResults);

    // Make the final request with tool call results
    const finalResponse = await groq.chat.completions.create({
      model,
      messages,
      tools,
      temperature: 0.5,
      tool_choice: "auto",
      max_completion_tokens: 4096,
    });

    return finalResponse.choices[0].message.content;
  } catch (error) {
    console.error("An error occurred:", error);
    throw error; // Re-throw the error so it can be caught by the caller
  }
}

runWeatherAssistant()
  .then((result) => {
    console.log("Final result:", result);
  })
  .catch((error) => {
    console.error("Error in main execution:", error);
  });
```

When the model returns multiple tool calls in the `tool_calls` array, process all of them before making the second API call. This is much more efficient than processing tool calls one at a time.

## [Complete Multi-Tool Example with Agentic Loop](#complete-multitool-example-with-agentic-loop)

Here's a comprehensive example showing multiple tools working together in an agentic loop to solve a complex financial calculation. The agent autonomously decides which tools to use and when, iterating until it has enough information to provide the final answer:

Python

```
import json

from groq import Groq

client = Groq(api_key="your-api-key")

# ============================================================================
# Tool Implementations
# ============================================================================


def calculate(expression: str) -> str:
    """Evaluate a basic mathematical expression"""
    try:
        result = eval(expression)  # Use safe evaluation in production!
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})


def calculate_compound_interest(
    principal: float, rate: float, time: float, compounds_per_year: int = 12
) -> str:
    """Calculate compound interest on an investment"""
    amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * time)
    interest = amount - principal
    return json.dumps(
        {
            "principal": principal,
            "total_amount": round(amount, 2),
            "interest_earned": round(interest, 2),
        }
    )


def calculate_percentage(number: float, percentage: float) -> str:
    """Calculate what percentage of a number equals"""
    result = (percentage / 100) * number
    return json.dumps({"result": round(result, 2)})


# Function registry
available_functions = {
    "calculate": calculate,
    "calculate_compound_interest": calculate_compound_interest,
    "calculate_percentage": calculate_percentage,
}

# ============================================================================
# Tool Schemas
# ============================================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression like '25 * 4 + 10' or '(100 - 50) / 2'",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_compound_interest",
            "description": "Calculate compound interest on an investment",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {
                        "type": "number",
                        "description": "The initial investment amount",
                    },
                    "rate": {
                        "type": "number",
                        "description": "The annual interest rate as a decimal (e.g., 0.05 for 5%)",
                    },
                    "time": {
                        "type": "number",
                        "description": "The time period in years",
                    },
                    "compounds_per_year": {
                        "type": "integer",
                        "description": "Number of times interest compounds per year (default: 12)",
                        "default": 12,
                    },
                },
                "required": ["principal", "rate", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_percentage",
            "description": "Calculate what a percentage of a number equals",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "number", "description": "The base number"},
                    "percentage": {
                        "type": "number",
                        "description": "The percentage to calculate",
                    },
                },
                "required": ["number", "percentage"],
            },
        },
    },
]

# ============================================================================
# Agentic Loop with Multi-Tool Support
# ============================================================================

user_query = """I'm investing $10,000 at 5% annual interest for 10 years, 
compounded monthly. After 10 years, I want to withdraw 25% for a down payment. 
How much will my down payment be, and how much will remain invested?"""

messages = [
    {
        "role": "system",
        "content": "You are a financial calculator assistant. Use the provided tools to help with calculations.",
    },
    {"role": "user", "content": user_query},
]

print(f"User: {user_query}\n")

# Initial request
response = client.chat.completions.create(
    model="openai/gpt-oss-120b", messages=messages, tools=tools, tool_choice="auto"
)

# Multi-turn loop: Continue while model requests tool calls
max_iterations = 10
iteration = 0

while response.choices[0].message.tool_calls and iteration < max_iterations:
    iteration += 1
    messages.append(response.choices[0].message)

    print(
        f"Iteration {iteration}: Model called {len(response.choices[0].message.tool_calls)} tool(s)"
    )

    # Handle all tool calls from this turn
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"  → {function_name}({function_args})")

        # Execute the function
        function_to_call = available_functions[function_name]
        function_response = function_to_call(**function_args)

        print(f"    ← {function_response}")

        # Add tool result to conversation
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_response,
            }
        )

    # Next turn with tool results
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    print()

# Final answer
print(f"Assistant: {response.choices[0].message.content}")

# Expected output:
# Iteration 1: Model called 1 tool(s)
#   → calculate_compound_interest({'principal': 10000, 'rate': 0.05, 'time': 10, 'compounds_per_year': 12})
#     ← {"principal": 10000, "total_amount": 16470.09, "interest_earned": 6470.09}
#
# Iteration 2: Model called 1 tool(s)
#   → calculate_percentage({'number': 16470.09, 'percentage': 25})
#     ← {"result": 4117.52}
#
# Iteration 3: Model called 1 tool(s)
#   → calculate({'expression': '16470.09 - 4117.52'})
#     ← {"result": 12352.57}
#
# Assistant: After 10 years, your $10,000 investment at 5% annual interest compounded monthly
# will grow to $16,470.09. Your 25% down payment will be $4,117.52, and you'll have $12,352.57
# remaining invested.
```

```
import Groq from "groq-sdk";

const client = new Groq({ apiKey: "your-api-key" });

// ============================================================================
// Tool Implementations
// ============================================================================

function calculate(expression) {
  try {
    // Use safe evaluation in production!
    const result = eval(expression);
    return JSON.stringify({ result });
  } catch (error) {
    return JSON.stringify({ error: error.message });
  }
}

function calculateCompoundInterest(
  principal,
  rate,
  time,
  compoundsPerYear = 12,
) {
  const amount =
    principal * Math.pow(1 + rate / compoundsPerYear, compoundsPerYear * time);
  const interest = amount - principal;
  return JSON.stringify({
    principal,
    total_amount: Math.round(amount * 100) / 100,
    interest_earned: Math.round(interest * 100) / 100,
  });
}

function calculatePercentage(number, percentage) {
  const result = (percentage / 100) * number;
  return JSON.stringify({ result: Math.round(result * 100) / 100 });
}

// Function registry
const availableFunctions = {
  calculate,
  calculate_compound_interest: calculateCompoundInterest,
  calculate_percentage: calculatePercentage,
};

// ============================================================================
// Tool Schemas
// ============================================================================

const tools = [
  {
    type: "function",
    function: {
      name: "calculate",
      description:
        "Evaluate a mathematical expression like '25 * 4 + 10' or '(100 - 50) / 2'",
      parameters: {
        type: "object",
        properties: {
          expression: {
            type: "string",
            description: "The mathematical expression to evaluate",
          },
        },
        required: ["expression"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "calculate_compound_interest",
      description: "Calculate compound interest on an investment",
      parameters: {
        type: "object",
        properties: {
          principal: {
            type: "number",
            description: "The initial investment amount",
          },
          rate: {
            type: "number",
            description:
              "The annual interest rate as a decimal (e.g., 0.05 for 5%)",
          },
          time: {
            type: "number",
            description: "The time period in years",
          },
          compounds_per_year: {
            type: "integer",
            description:
              "Number of times interest compounds per year (default: 12)",
            default: 12,
          },
        },
        required: ["principal", "rate", "time"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "calculate_percentage",
      description: "Calculate what a percentage of a number equals",
      parameters: {
        type: "object",
        properties: {
          number: {
            type: "number",
            description: "The base number",
          },
          percentage: {
            type: "number",
            description: "The percentage to calculate",
          },
        },
        required: ["number", "percentage"],
      },
    },
  },
];

// ============================================================================
// Agentic Loop with Multi-Tool Support
// ============================================================================

async function runMultiToolAgent() {
  const userQuery = `I'm investing $10,000 at 5% annual interest for 10 years, 
compounded monthly. After 10 years, I want to withdraw 25% for a down payment. 
How much will my down payment be, and how much will remain invested?`;

  const messages = [
    {
      role: "system",
      content:
        "You are a financial calculator assistant. Use the provided tools to help with calculations.",
    },
    {
      role: "user",
      content: userQuery,
    },
  ];

  console.log(`User: ${userQuery}\n`);

  // Initial request
  let response = await client.chat.completions.create({
    model: "openai/gpt-oss-120b",
    messages,
    tools,
    tool_choice: "auto",
  });

  // Multi-turn loop: Continue while model requests tool calls
  const maxIterations = 10;
  let iteration = 0;

  while (response.choices[0].message.tool_calls && iteration < maxIterations) {
    iteration++;
    messages.push(response.choices[0].message);

    console.log(
      `Iteration ${iteration}: Model called ${response.choices[0].message.tool_calls.length} tool(s)`,
    );

    // Handle all tool calls from this turn
    for (const toolCall of response.choices[0].message.tool_calls) {
      const functionName = toolCall.function.name;
      const functionArgs = JSON.parse(toolCall.function.arguments);

      console.log(`  → ${functionName}(${JSON.stringify(functionArgs)})`);

      // Execute the function with proper argument spreading
      // Different functions expect different argument structures
      const functionToCall = availableFunctions[functionName];
      let functionResponse;

      if (functionName === "calculate") {
        functionResponse = functionToCall(functionArgs.expression);
      } else if (functionName === "calculate_compound_interest") {
        functionResponse = functionToCall(
          functionArgs.principal,
          functionArgs.rate,
          functionArgs.time,
          functionArgs.compounds_per_year,
        );
      } else if (functionName === "calculate_percentage") {
        functionResponse = functionToCall(
          functionArgs.number,
          functionArgs.percentage,
        );
      }

      console.log(`    ← ${functionResponse}`);

      // Add tool result to conversation
      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        name: functionName,
        content: functionResponse,
      });
    }

    // Next turn with tool results
    response = await client.chat.completions.create({
      model: "openai/gpt-oss-120b",
      messages,
      tools,
      tool_choice: "auto",
    });
    console.log();
  }

  // Final answer
  console.log(`Assistant: ${response.choices[0].message.content}`);
}

runMultiToolAgent();

// Expected output:
// Iteration 1: Model called 1 tool(s)
//   → calculate_compound_interest({"principal":10000,"rate":0.05,"time":10,"compounds_per_year":12})
//     ← {"principal":10000,"total_amount":16470.09,"interest_earned":6470.09}
//
// Iteration 2: Model called 1 tool(s)
//   → calculate_percentage({"number":16470.09,"percentage":25})
//     ← {"result":4117.52}
//
// Iteration 3: Model called 1 tool(s)
//   → calculate({"expression":"16470.09 - 4117.52"})
//     ← {"result":12352.57}
//
// Assistant: After 10 years, your $10,000 investment at 5% annual interest compounded monthly
// will grow to $16,470.09. Your 25% down payment will be $4,117.52, and you'll have $12,352.57
// remaining invested.
```

This example demonstrates:

* **Multiple tool implementations** \- Three different calculation tools
* **Function registry pattern** \- Scalable way to map function names to implementations
* **Multi-turn agentic loop** \- Agent calls tools iteratively until goal is achieved
* **Complex problem solving** \- Query requires 3 different tools across 3 iterations
* **Proper conversation threading** \- All messages and tool results are properly connected

The agent breaks down the complex query into steps, calling tools as needed, and uses previous results to inform next steps - true agentic behavior.

## [Controlling Tool Use Behavior](#controlling-tool-use-behavior)

The `tool_choice` parameter controls how the model uses tools:

### [tool\_choice: "auto" (Default)](#toolchoice-auto-default)

The model decides whether to use tools based on the query:

JSON

```
{
  "tool_choice": "auto"
}
```

**Behavior:** The model will use tools only when it determines they're needed for the query.

### [tool\_choice: "required"](#toolchoice-required)

Forces the model to use at least one tool:

JSON

```
{
  "tool_choice": "required"
}
```

**Behavior:** Use this when you want to ensure a tool is always called. If the model decides not to use any tools, the API will return an error (400 Bad Request). To avoid this, you should steer the model to use a tool in your prompt. In some instances, retrying with a lower temperature may help.

### [tool\_choice: "none"](#toolchoice-none)

Prevents the model from using any tools:

JSON

```
{
  "tool_choice": "none"
}
```

**Behavior:** The model will not use tools, even if they're provided. **Note:** With some models, the model may still attempt to use tools despite this setting - if this happens, the API will return an error (400 Bad Request) since tool execution was blocked. This behavior varies by model. To avoid this, you should steer the model to avoid using tools in your prompt. In some instances, retrying with a lower temperature may help.

### [tool\_choice: {"type": "function", "function": {"name": "function\_name"}}](#toolchoice-type-function-function-name-functionname)

Forces the model to use a specific tool:

JSON

```
{
  "tool_choice": {
    "type": "function",
    "function": {"name": "get_weather"}
  }
}
```

**Behavior:** The model must call the specified function. If it tries to call a different function or no function at all, the API will return an error (400 Bad Request).

## [Streaming Tool Use](#streaming-tool-use)

You can stream tool use responses to provide faster feedback to users:

Python

```
import random
from groq import Groq
import json

client = Groq()

"""
========================================
Conversation Engine
========================================
"""

async def main():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "What is the weather in San Francisco and Tokyo?",
        },
    ]

    max_turns = 10
    turn_number = 0
    while turn_number < max_turns:
        stream = client.chat.completions.create(
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_weather",
                        "description": "Get the current weather in a given location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city and state, e.g. San Francisco, CA",
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                },
                            },
                            "required": ["location"],
                        },
                    },
                }
            ],
            model="openai/gpt-oss-120b",
            temperature=0.5,
            stream=True,
        )

        collected_content = ""
        collected_tool_calls = []
        finish_reason = None

        for chunk in stream:
            if chunk.choices[0].delta.content:
                collected_content += chunk.choices[0].delta.content
            if chunk.choices[0].delta.tool_calls:
                collected_tool_calls.extend(chunk.choices[0].delta.tool_calls)
            if chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason


        messages.append({
            "role": "assistant",
            "content": collected_content,
            "tool_calls": collected_tool_calls,
        })

        if collected_tool_calls and finish_reason == "tool_calls":
            print(f"Turn {turn_number + 1} of {max_turns}: Executing tool calls")
            results = execute_tool_calls(collected_tool_calls)
            # append results to messages
            messages.extend(results)
            turn_number += 1
            continue
        elif collected_content and finish_reason == "stop":
            print(f"Turn {turn_number + 1} of {max_turns}: Finished")
            print(collected_content)
            return
        else:
            print(f"Turn {turn_number + 1} of {max_turns}: Unknown finish reason: {finish_reason}")
            return
    print(f"Turn {turn_number + 1} of {max_turns}: Exhausted all turns")


"""
========================================
Tool Definitions
========================================
"""

def get_current_weather(location: str, unit: str = "celsius") -> str:
    random_number = random.randint(20, 40) if unit == "celsius" else random.randint(60, 100)
    return f"The current weather in {location} is {random_number} {unit}."


tool_call_map = {
    "get_current_weather": get_current_weather,
}


"""
========================================
Tool Execution
========================================
"""

def execute_tool_calls(tool_calls: list[dict]) -> list[dict]:
    results = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        tool_call_id = tool_call.id

        print(f"Executing tool call: {function_name} with arguments: {function_args}")

        if function_name not in tool_call_map:
            raise ValueError(f"Unknown tool call: {function_name}")

        function_response = tool_call_map[function_name](https://console.groq.com/docs/tool-use/**function_args)

        results.append(
            {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
        )
    return results


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

```
import Groq from "groq-sdk";

const client = new Groq();

/*
========================================
Conversation Engine
========================================
*/

async function main() {
  const messages = [
    {
      role: "system",
      content: "You are a helpful assistant.",
    },
    {
      role: "user",
      content: "What is the weather in San Francisco and Tokyo?",
    },
  ];

  const maxTurns = 10;
  let turnNumber = 0;

  while (turnNumber < maxTurns) {
    const stream = await client.chat.completions.create({
      messages: messages,
      tools: [
        {
          type: "function",
          function: {
            name: "get_current_weather",
            description: "Get the current weather in a given location",
            parameters: {
              type: "object",
              properties: {
                location: {
                  type: "string",
                  description: "The city and state, e.g. San Francisco, CA",
                },
                unit: {
                  type: "string",
                  enum: ["celsius", "fahrenheit"],
                },
              },
              required: ["location"],
            },
          },
        },
      ],
      model: "openai/gpt-oss-120b",
      temperature: 0.5,
      stream: true,
    });

    let collectedContent = "";
    let collectedToolCalls = [];
    let finishReason = null;

    for await (const chunk of stream) {
      if (chunk.choices[0].delta.content) {
        collectedContent += chunk.choices[0].delta.content;
      }
      if (chunk.choices[0].delta.tool_calls) {
        collectedToolCalls.push(...chunk.choices[0].delta.tool_calls);
      }
      if (chunk.choices[0].finish_reason) {
        finishReason = chunk.choices[0].finish_reason;
      }
    }

    messages.push({
      role: "assistant",
      content: collectedContent,
      tool_calls: collectedToolCalls,
    });

    if (collectedToolCalls.length > 0 && finishReason === "tool_calls") {
      console.log(
        `Turn ${turnNumber + 1} of ${maxTurns}: Executing tool calls`,
      );
      const results = executeToolCalls(collectedToolCalls);
      messages.push(...results);
      turnNumber++;
      continue;
    } else if (collectedContent && finishReason === "stop") {
      console.log(`Turn ${turnNumber + 1} of ${maxTurns}: Finished`);
      console.log(collectedContent);
      return;
    } else {
      console.log(
        `Turn ${
          turnNumber + 1
        } of ${maxTurns}: Unknown finish reason: ${finishReason}`,
      );
      return;
    }
  }
  console.log(`Turn ${turnNumber + 1} of ${maxTurns}: Exhausted all turns`);
}

/*
========================================
Tool Definitions
========================================
*/

function getCurrentWeather(location, unit = "celsius") {
  const randomNumber =
    unit === "celsius"
      ? Math.floor(Math.random() * (40 - 20 + 1)) + 20
      : Math.floor(Math.random() * (100 - 60 + 1)) + 60;
  return `The current weather in ${location} is ${randomNumber} ${unit}.`;
}

const toolCallMap = {
  get_current_weather: getCurrentWeather,
};

/*
========================================
Tool Execution
========================================
*/

function executeToolCalls(toolCalls) {
  const results = [];
  for (const toolCall of toolCalls) {
    const functionName = toolCall.function.name;
    const functionArgs = JSON.parse(toolCall.function.arguments);
    const toolCallId = toolCall.id;

    console.log(
      `Executing tool call: ${functionName} with arguments:`,
      functionArgs,
    );

    if (!(functionName in toolCallMap)) {
      throw new Error(`Unknown tool call: ${functionName}`);
    }

    const functionResponse = toolCallMap[functionName](https://console.groq.com/docs/tool-use/functionArgs.location,%20%20%20%20%20%20functionArgs.unit,);

    results.push({
      tool_call_id: toolCallId,
      role: "tool",
      name: functionName,
      content: functionResponse,
    });
  }
  return results;
}

main();
```

## [Structured Outputs with Type Safety](#structured-outputs-with-type-safety)

For more complex tools with strict schema requirements, we recommend using type-safe libraries:

### [Python: Instructor](#python-instructor)

Use [Instructor](https://python.useinstructor.com/hub/groq/) for Pydantic-based type safety:

Python

```
# pip install instructor pydantic groq
import instructor
from groq import Groq
from pydantic import BaseModel, Field

# Define the tool schema
tool_schema = {
    "name": "get_weather_info",
    "description": "Get the weather information for any location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location for which we want to get the weather information (e.g., New York)",
            }
        },
        "required": ["location"],
    },
}


# Define the Pydantic model for the tool call
class ToolCall(BaseModel):
    input_text: str = Field(description="The user's input text")
    tool_name: str = Field(description="The name of the tool to call")
    tool_parameters: str = Field(description="JSON string of tool parameters")


class ResponseModel(BaseModel):
    tool_calls: list[ToolCall]


# Patch Groq() with instructor
client = instructor.from_groq(Groq(), mode=instructor.Mode.JSON)


def run_conversation(user_prompt):
    # Prepare the messages
    messages = [
        {
            "role": "system",
            "content": f"You are an assistant that can use tools. You have access to the following tool: {tool_schema}",
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    # Make the Groq API call
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=ResponseModel,
        messages=messages,
        temperature=0.5,
        max_completion_tokens=1000,
    )

    return response.tool_calls


# Example usage
user_prompt = "What's the weather like in San Francisco?"
tool_calls = run_conversation(user_prompt)

for call in tool_calls:
    print(f"Input: {call.input_text}")
    print(f"Tool: {call.tool_name}")
    print(f"Parameters: {call.tool_parameters}")
    print()
```

**Benefits:**

* **Type Safety** \- Pydantic models ensure outputs match expected structure
* **Automatic Validation** \- Invalid outputs are caught immediately
* **Better Reliability** \- Reduces errors from malformed tool calls

For more examples, see the [Groq API Cookbook tutorial on structured outputs](https://github.com/groq/groq-api-cookbook/tree/main/tutorials/05-structured-output/structured-output-instructor/structured%5Foutput%5Finstructor.ipynb).

### [TypeScript: Zod](#typescript-zod)

For TypeScript users, use [Zod](https://zod.dev/) for schema validation:

TypeScript

```
// npm install groq-sdk zod
import Groq from "groq-sdk";
import { z } from "zod";

const client = new Groq();

// Define your tool's output schema
const WeatherSchema = z.object({
  location: z.string(),
  temperature: z.number(),
  conditions: z.string(),
  humidity: z.number().optional(),
});

// Convert Zod schema to JSON Schema (requires zod v4+)
const jsonSchema = z.toJSONSchema(WeatherSchema);

// Use the schema for type-safe parsing
const response = await client.chat.completions.create({
  model: "openai/gpt-oss-120b",
  messages: [
    {
      role: "user",
      content: "What's the weather in San Francisco?",
    },
  ],
  response_format: {
    type: "json_schema",
    json_schema: {
      name: "weather",
      schema: jsonSchema,
    },
  },
});

// Parse and validate the response
const weather = WeatherSchema.parse(
  JSON.parse(response.choices[0].message.content),
);
console.log(weather); // Type-safe!
```

**Benefits:**

* **TypeScript Integration** \- Full type inference and autocomplete
* **Runtime Validation** \- Catches invalid data at runtime
* **Schema-First Design** \- Define once, use everywhere

## [Error Handling](#error-handling)

Robust error handling is crucial for production tool use. Groq API validates tool call objects and provides specific error feedback to help you build reliable agentic systems.

### [Groq's Tool Call Validation](#groqs-tool-call-validation)

Groq API verifies that the model generates valid tool call objects. When a model fails to generate a valid tool call object, Groq API returns a **400 error** with an explanation in the `"failed_generation"` field of the response body.

**Example error response:**

JSON

```
{
  "error": {
    "message": "Invalid tool call generated",
    "type": "invalid_request_error",
    "failed_generation": {
      "reason": "Tool call arguments are not valid JSON",
      "tool_call_id": "call_abc123",
      "attempted_arguments": "{'location': 'New York'}"
    }
  }
}
```

### [Retry Strategy for Failed Tool Calls](#retry-strategy-for-failed-tool-calls)

When tool call generation fails, implement a retry strategy with adjusted temperature:

Python

```
from groq import Groq

client = Groq()

def call_with_tools_and_retry(messages, tools, max_retries=3):
    """Call model with tools, retrying with adjusted temperature on failure"""
    
    # Start with moderate temperature
    temperature = 1.0
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=tools,
                temperature=temperature
            )
            return response
            
        except Exception as e:
            # Check if this is a tool call generation error
            if hasattr(e, 'status_code') and e.status_code == 400:
                if attempt < max_retries - 1:
                    # Decrease temperature for next attempt to reduce hallucinations
                    temperature = max(temperature - 0.2, 0.2)
                    print(f"Tool call failed, retrying with lower temperature {temperature}")
                    continue
            
            # If not a tool call error or out of retries, raise
            raise e
    
    raise Exception("Failed to generate valid tool calls after retries")
```

```
import Groq from "groq-sdk";

const client = new Groq();

async function callWithToolsAndRetry(messages, tools, maxRetries = 3) {
  /**
   * Call model with tools, retrying with adjusted temperature on failure
   */

  // Start with moderate temperature
  let temperature = 1.0;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await client.chat.completions.create({
        model: "openai/gpt-oss-120b",
        messages: messages,
        tools: tools,
        temperature: temperature,
      });
      return response;
    } catch (e) {
      // Check if this is a tool call generation error
      if (e.status === 400) {
        if (attempt < maxRetries - 1) {
          // Decrease temperature for next attempt to reduce hallucinations
          temperature = Math.max(temperature - 0.2, 0.2);
          console.log(
            `Tool call failed, retrying with lower temperature ${temperature}`,
          );
          continue;
        }
      }

      // If not a tool call error or out of retries, throw
      throw e;
    }
  }

  throw new Error("Failed to generate valid tool calls after retries");
}

export { callWithToolsAndRetry };
```

**Why lower temperature on retry?**

* **Lower temperature (0.0-1)**: More deterministic and reduces hallucinations, which is critical for structured outputs like tool calls
* **Higher temperature (1+)**: More creative but increases randomness, which can lead to invalid JSON or malformed tool calls
* When tool call generation fails, the model is likely hallucinating or generating invalid structured output. Decreasing temperature makes the model more focused and deterministic, reducing the chance of malformed tool calls on subsequent attempts

### [Handle Missing Tool Calls](#handle-missing-tool-calls)

Python

```
from groq import Groq

client = Groq()

def handle_response(response):
    """Handle a response that may or may not contain tool calls"""
    
    response_message = response.choices[0].message

    if not response_message.tool_calls:
        # Model didn't use tools, return direct response
        return response_message.content

    # Process tool calls
    # ... (tool execution code here)
```

```
import Groq from "groq-sdk";

const client = new Groq();

function handleResponse(response) {
  /**
   * Handle a response that may or may not contain tool calls
   */

  const responseMessage = response.choices[0].message;

  if (!responseMessage.tool_calls) {
    // Model didn't use tools, return direct response
    return responseMessage.content;
  }

  // Process tool calls
  // ... (tool execution code here)
}

export { handleResponse };
```

### [Handle Tool Execution Errors](#handle-tool-execution-errors)

When a tool execution fails, return an error message to the model:

Python

```
import json

def execute_tool_with_error_handling(tool_call, tool_name, execute_tool):
    """Execute a tool and handle errors gracefully"""
    
    try:
        result = execute_tool(tool_call)
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_name,
            "content": str(result)
        }
    except Exception as e:
        # Return error to model so it can adjust its approach
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_name,
            "content": json.dumps({
                "error": str(e),
                "is_error": True
            })
        }
```

```
function executeToolWithErrorHandling(toolCall, toolName, executeTool) {
  /**
   * Execute a tool and handle errors gracefully
   */

  try {
    const result = executeTool(toolCall);
    return {
      tool_call_id: toolCall.id,
      role: "tool",
      name: toolName,
      content: String(result),
    };
  } catch (e) {
    // Return error to model so it can adjust its approach
    return {
      tool_call_id: toolCall.id,
      role: "tool",
      name: toolName,
      content: JSON.stringify({
        error: e.message,
        is_error: true,
      }),
    };
  }
}

export { executeToolWithErrorHandling };
```

The model can then inform the user about the error or try alternative approaches.

### [Validate Tool Call Arguments](#validate-tool-call-arguments)

Always validate and sanitize arguments before executing tools:

Python

```
import json

def validate_and_parse_tool_arguments(tool_call):
    """Validate and sanitize tool call arguments"""
    
    try:
        function_args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        # Handle malformed JSON
        return None, json.dumps({
            "error": f"Invalid JSON in tool arguments: {str(e)}",
            "is_error": True
        })

    # Validate required parameters
    if "location" not in function_args:
        return None, json.dumps({
            "error": "Missing required parameter: location",
            "is_error": True
        })

    # Sanitize inputs
    location = str(function_args["location"]).strip()
    if not location:
        return None, json.dumps({
            "error": "Location cannot be empty",
            "is_error": True
        })
    
    return function_args, None
```

```
function validateAndParseToolArguments(toolCall) {
  /**
   * Validate and sanitize tool call arguments
   */

  let functionArgs;
  try {
    functionArgs = JSON.parse(toolCall.function.arguments);
  } catch (e) {
    // Handle malformed JSON
    return [
      null,
      JSON.stringify({
        error: `Invalid JSON in tool arguments: ${e.message}`,
        is_error: true,
      }),
    ];
  }

  // Validate required parameters
  if (!("location" in functionArgs)) {
    return [
      null,
      JSON.stringify({
        error: "Missing required parameter: location",
        is_error: true,
      }),
    ];
  }

  // Sanitize inputs
  const location = String(functionArgs.location).trim();
  if (!location) {
    return [
      null,
      JSON.stringify({
        error: "Location cannot be empty",
        is_error: true,
      }),
    ];
  }

  return [functionArgs, null];
}

export { validateAndParseToolArguments };
```

### [Complete Error Handling Example](#complete-error-handling-example)

Here's a production-ready example with comprehensive error handling:

Python

```
from groq import Groq
import json

client = Groq()

def call_with_tools_and_retry(messages, tools, max_retries=3):
    """Call model with tools, retrying with adjusted temperature on failure"""
    temperature = 0.2
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=tools,
                temperature=temperature
            )
            return response
        except Exception as e:
            if hasattr(e, 'status_code') and e.status_code == 400:
                if attempt < max_retries - 1:
                    temperature = min(temperature + 0.2, 1.0)
                    print(f"Tool call failed, retrying with temperature {temperature}")
                    continue
            raise e
    
    raise Exception("Failed to generate valid tool calls after retries")


def run_tool_calling_with_error_handling(user_query, tools, available_functions):
    """Production-grade tool calling with error handling"""
    
    messages = [{"role": "user", "content": user_query}]
    max_iterations = 10
    
    for iteration in range(max_iterations):
        try:
            # Try to get tool calls with retry logic
            response = call_with_tools_and_retry(messages, tools)
            
            # Check if we're done
            if not response.choices[0].message.tool_calls:
                return response.choices[0].message.content
            
            # Add assistant message
            messages.append(response.choices[0].message)
            
            # Execute each tool call
            for tool_call in response.choices[0].message.tool_calls:
                try:
                    function_name = tool_call.function.name
                    
                    # Validate function exists
                    if function_name not in available_functions:
                        raise ValueError(f"Unknown function: {function_name}")
                    
                    # Parse and validate arguments
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute function
                    function_to_call = available_functions[function_name]
                    result = function_to_call(**function_args)
                    
                    # Add successful result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result)
                    })
                    
                except Exception as e:
                    # Add error result for this tool call
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps({
                            "error": str(e),
                            "is_error": True
                        })
                    })
        
        except Exception as e:
            return f"Error in tool calling loop: {str(e)}"
    
    return "Max iterations reached without completing task"
```

```
import Groq from "groq-sdk";

const client = new Groq();

async function callWithToolsAndRetry(messages, tools, maxRetries = 3) {
  /**
   * Call model with tools, retrying with adjusted temperature on failure
   */
  let temperature = 0.2;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await client.chat.completions.create({
        model: "openai/gpt-oss-120b",
        messages: messages,
        tools: tools,
        temperature: temperature,
      });
      return response;
    } catch (e) {
      if (e.status === 400) {
        if (attempt < maxRetries - 1) {
          temperature = Math.min(temperature + 0.2, 1.0);
          console.log(
            `Tool call failed, retrying with temperature ${temperature}`
          );
          continue;
        }
      }
      throw e;
    }
  }

  throw new Error("Failed to generate valid tool calls after retries");
}

async function runToolCallingWithErrorHandling(
  userQuery,
  tools,
  availableFunctions
) {
  /**
   * Production-grade tool calling with error handling
   */

  const messages = [{ role: "user", content: userQuery }];
  const maxIterations = 10;

  for (let iteration = 0; iteration < maxIterations; iteration++) {
    try {
      // Try to get tool calls with retry logic
      const response = await callWithToolsAndRetry(messages, tools);

      // Check if we're done
      if (!response.choices[0].message.tool_calls) {
        return response.choices[0].message.content;
      }

      // Add assistant message
      messages.push(response.choices[0].message);

      // Execute each tool call
      for (const toolCall of response.choices[0].message.tool_calls) {
        try {
          const functionName = toolCall.function.name;

          // Validate function exists
          if (!(functionName in availableFunctions)) {
            throw new Error(`Unknown function: ${functionName}`);
          }

          // Parse and validate arguments
          const functionArgs = JSON.parse(toolCall.function.arguments);

          // Execute function
          const functionToCall = availableFunctions[functionName];
          const result = functionToCall(functionArgs);

          // Add successful result
          messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            name: functionName,
            content: String(result),
          });
        } catch (e) {
          // Add error result for this tool call
          messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            name: functionName,
            content: JSON.stringify({
              error: e.message,
              is_error: true,
            }),
          });
        }
      }
    } catch (e) {
      return `Error in tool calling loop: ${e.message}`;
    }
  }

  return "Max iterations reached without completing task";
}

export { runToolCallingWithErrorHandling };
```

## [Best Practices](#best-practices)

### [1\. Write Clear Tool Descriptions](#1-write-clear-tool-descriptions)

The model relies on descriptions to understand when and how to use tools:

**❌ Bad:**

JSON

```
{
  "name": "get_data",
  "description": "Gets data"
}
```

**✅ Good:**

JSON

```
{
  "name": "get_customer_order_history",
  "description": "Retrieves the complete order history for a customer by their email address. Returns order IDs, dates, amounts, and status. Use this when the user asks about their past orders or purchases."
}
```

### [2\. Use Descriptive Parameter Names](#2-use-descriptive-parameter-names)

**❌ Bad:**

JSON

```
{
  "properties": {
    "q": { "type": "string" },
    "n": { "type": "integer" }
  }
}
```

**✅ Good:**

JSON

```
{
  "properties": {
    "search_query": {
      "type": "string",
      "description": "The search term to look for in product names and descriptions"
    },
    "max_results": {
      "type": "integer",
      "description": "Maximum number of results to return (1-50)"
    }
  }
}
```

### [3\. Return Structured Data](#3-return-structured-data)

Return tool results in a structured format when possible:

**❌ Bad:**

Python

```
return f"Weather is {temp} degrees and {condition}"
```

```
return `Weather is ${temp} degrees and ${condition}`;
```

**✅ Good:**

Python

```
return json.dumps({
    "temperature": temp,
    "unit": "fahrenheit",
    "condition": condition,
    "humidity": humidity,
    "timestamp": datetime.now().isoformat()
})
```

```
return JSON.stringify({
    temperature: temp,
    unit: "fahrenheit",
    condition: condition,
    humidity: humidity,
    timestamp: new Date().toISOString()
});
```

### [4\. Limit Tool Count](#4-limit-tool-count)

Avoid overwhelming the model with too many tools in a single request:

* **Optimal**: 3-5 tools per request
* **Maximum**: 10-15 tools for more capable models

For large tool libraries, use a routing system to select relevant tools based on the query.

### [5\. Use System Prompts Effectively](#5-use-system-prompts-effectively)

Guide the model's tool use behavior with clear system prompts:

Python

```
{
    "role": "system",
    "content": """You are a customer service assistant. 
    
    Use the get_order_status tool when customers ask about orders.
    Use the get_product_info tool when customers ask about products.
    Always confirm the order ID or product SKU before calling tools.
    If a tool returns an error, apologize and ask the user for clarification."""
}
```

```
{
    role: "system",
    content: `You are a customer service assistant. 
    
    Use the get_order_status tool when customers ask about orders.
    Use the get_product_info tool when customers ask about products.
    Always confirm the order ID or product SKU before calling tools.
    If a tool returns an error, apologize and ask the user for clarification.`
}
```

## [Next Steps](#next-steps)

* **[Groq Built-In Tools](https://console.groq.com/docs/tool-use/built-in-tools)** \- Use web search, code execution, and more without any setup
* **[Remote Tools and MCP](https://console.groq.com/docs/tool-use/remote-mcp)** \- Learn about connecting to external tool providers via MCP
* **[Compound Systems](https://console.groq.com/docs/compound)** \- Use Groq's purpose-built agentic systems with built-in tools
* **[Groq API Cookbook](https://github.com/groq/groq-api-cookbook/blob/main/tutorials/parallel-tool-use/parallel-tool-use.ipynb)** \- More examples of parallel tool use