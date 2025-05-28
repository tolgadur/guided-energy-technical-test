from openai import OpenAI

client = OpenAI()


def ask_gpt(prompt):
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a weather assistant that gives queries about the weather",
        input=prompt,
    )

    return response.output_text
