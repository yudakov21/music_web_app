import openai


class OpenAIClient:
    def __init__(self, openai_key: str):
        openai.api_key = openai_key

    def analyze_text(self, text: str, level: str, language: str):
        prompt = (
            f""""You are a highly skilled language teacher. 
            Your task is to translate the following text into the candidate's target language, 
            and then explain the translated text in their native language. 
            Please consider the candidate's proficiency level when translating and explaining."""
            f"Translate text based on candidate's proficiency level:\n{text}\n\n"
            f"Explain translated text in the user's native language : {language}\n"
            f"Candidate's proficiency level: {level}\n"
        )

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                        "content": "You are an experienced language teacher."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content
            return {
                "analysis": reply.strip()
            }
        except openai.OpenAIError as e:
            raise RuntimeError(f"Error OpenAI API: {str(e)}")

    def chat(self, message: str, history: list):
        if history is None:
            history = []

        messages = [
            {"role": "system", "content": "You are a helpful assistant and an experienced language teacher."}]
        messages += history
        messages.append({"role": "user", "content": message})

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages)
            reply = response.choices[0].message.content

            return {
                "reply": reply.strip(),
                "history": history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
            }
        except openai.OpenAIError as e:
            raise RuntimeError(f"Error OpenAI API: {str(e)}")
