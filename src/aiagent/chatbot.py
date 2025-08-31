import chainlit as cl
import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel,function_tool
from agents.run import RunConfig
import requests

load_dotenv()

@function_tool
def get_weather(city:str)->str:
    """
    Get the current weather for a given city. and provide  weather details and humidity for any city
    """
    
    API_Key = '5be9ec2f20a42c801a00ede872a61e48'
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_Key}&units=metric"
    weather_data = requests.get(base_url).json()
    return f"The current weather in {city} is {weather_data['main']['temp']}°C."




gemini_api_key = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client
    )

config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )

agent1 = Agent(
        name="Assistant", 
        instructions="You are a Amsal Assistant.", 
        model=model,
        tools=[get_weather]
        )







@cl.on_chat_start
async def start():
   # Initialize an empty chat history in the session.
    cl.user_session.set("history", [])
    await cl.Message(content="Hi ! How can I help you today?").send()





@cl.on_message
async def main(message: cl.Message):
    # Retrieve the chat history from the session.
    history = cl.user_session.get("history") or []


    # Append the user's message to the history.
    history.append({"role": "user", "content": message.content})

    # Create a new message object for streaming
    msg = cl.Message(content="")
    await msg.send()

    result=  Runner.run_streamed(
     agent1,
     input=history,
     run_config=config,
    )

    async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, 'delta'):
                token = event.data.delta
                await msg.stream_token(token)


    history.append({"role": "assistant", "content": result.final_output})

    # Update the session with the new history
    cl.user_session.set("history", history)


  