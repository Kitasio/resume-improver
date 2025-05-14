from openai import OpenAI
from pydantic import BaseModel

DEFAULT_MODEL = "o3-mini"


class HtmlAdapter(BaseModel):
    tuning_result: str
    html_template: str

    def run(self) -> str:
        """
        Uses an LLM to insert the plain text tuning result into the HTML template,
        replacing placeholder data.
        """
        client = OpenAI()

        system_message = """
        You are an expert web developer assistant. Your task is to take a plain text CV and an HTML template, and generate a new HTML document. The new document should use the structure and styling of the provided HTML template, but replace all placeholder content (like names, addresses, fake experience) with the actual content from the plain text CV. Maintain the original HTML structure, classes, and styling as much as possible. Only return the complete HTML document.
        """

        user_message = f"""
        <plain_text_cv>
        {self.tuning_result}
        </plain_text_cv>

        <html_template>
        {self.html_template}
        </html_template>

        Generate the new HTML document with the CV content inserted into the template.
        """

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,  # Using the same model as Tuner for consistency
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        # Extract the content from the response
        generated_html = response.choices[0].message.content
        if not generated_html:
            raise Exception(
                "Failed to extract message content from LLM response for HTML generation"
            )

        return generated_html


class ResumeImprover(BaseModel):
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
            model=DEFAULT_MODEL,
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
