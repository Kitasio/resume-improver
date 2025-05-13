from openai import OpenAI
from pydantic import BaseModel


class Tuner(BaseModel):
    cv_input: str
    jd_input: str

    def run(self) -> str:
        """
        Tunes the CV based on the job description using an LLM.
        """
        system_message = """
        You are a helpful assistant that tailors CVs to best match specific job descriptions. When given a candidate’s CV and a target job description, your task is to revise the CV so that it strongly aligns with the role and stands out to hiring managers.

        Instructions:

        Focus on optimizing the CV for the target job by emphasizing the most relevant skills, experiences, and accomplishments.

        Reword, reorganize, condense, or expand content as needed to align with the job description.

        Use clear, professional language and formatting.

        You may adjust tone and style if it improves clarity or alignment with the job, but maintaining readability and impact is the priority.

        Do not invent new experiences or qualifications—only enhance or infer from existing content.

        Deliver a polished, targeted CV with no explanations or commentary—only return the revised CV.
        """

        user_message = f"""
        <CV>
        {self.cv_input}
        </CV>

        <job_description>
        {self.jd_input}
        </job_description>
        """

        client = OpenAI()

        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        # Extract the content from the response
        tuned_cv = response.choices[0].message.content
        if not tuned_cv:
            raise Exception("Failed to extract message content from LLM response")
        return tuned_cv
