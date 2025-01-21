import os

from dotenv import load_dotenv
from openai import OpenAI

client = OpenAI()
from typing import Optional

from agent import Agent
from pydantic import BaseModel
from tools import execute_tool_call, execute_tool_call_handoff, function_to_schema

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

SYSTEM_MESSAGE = (
    "You are a customer support agent for ACME Inc."
    "Always answer in a sentence or less."
    "Follow the following routine with the user:"
    "1. First, ask probing questions and understand the user's problem deeper.\n"
    " - unless the user has already provided a reason.\n"
    "2. Propose a fix (make one up).\n"
    "3. ONLY if not satesfied, offer a refund.\n"
    "4. If accepted, search for the ID and then execute refund."
    ""
)


class Response(BaseModel):
    agent: Optional[Agent]
    messages: list


def run_full_turn(system_message, messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_message} + messages],
    )
    message = response.choices[0].message
    messages.append(message)
    return message


def run_full_turn_with_tools(system_message, tools, messages):
    num_init_messages = len(messages)
    messages = messages.copy()
    while True:
        tool_schemas = [function_to_schema(tool) for tool in tools]
        tools_map = {tool.__name: tool for tool in tools}
        # get response
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)
        if message.content:
            print("Assistant:", message.content)
        if not message.tool_call:
            break
    # Handle tool_call
    for tool_call in message.tool_calls:
        result = execute_tool_call(tool_call, tools_map)
        result_msg = {"role": "tool", "tool_call_id": tool_call.id, "content": result}
        messages.append(result_msg)
    # return latest msg
    return messages[num_init_messages:]


def run_full_turn_agent(agent: Agent, messages):
    num_init_messages = len(messages)
    messages = messages.copy()
    while True:
        tool_schemas = [function_to_schema(tool) for tool in agent.tools]
        tools_map = {tool.__name__: tool for tool in agent.tools}
        response = client.chat.completions.create(
            model=agent.model,
            messages=[{"role": "system", "content": agent.instructions}] + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)
        if message.content:
            print("Assistant:", message.content)
        if not message.tool_calls:
            break
        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools_map)
            result_msg = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_msg)

    return messages[num_init_messages:]


def run_full_turn_agent_handoff(agent, messages):
    current_agent = agent
    num_init_messages = len(messages)
    messages = messages.copy()
    while True:
        tool_schemas = [function_to_schema(tool) for tool in current_agent.tools]
        tools = {tool.__name__: tool for tool in current_agent.tools}
        response = client.chat.completions.create(
            model=agent.model,
            messages=[{"role": "system", "content": current_agent.instructions}]
            + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print(f"{current_agent.name}:", message.content)
        if not message.tool_calls:
            break
        for tool_call in message.tool_calls:
            result = execute_tool_call_handoff(tool_call, tools, current_agent.name)
            if isinstance(result, Agent):
                current_agent = result
                result = (
                    f"Transfered to {current_agent.name}. Adopt persona immediately."
                )
            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_message)
    return Response(agent=current_agent, messages=messages[num_init_messages:])
