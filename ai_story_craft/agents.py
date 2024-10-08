from dataclasses import dataclass


@dataclass
class ProductManager:
    instructions: str = """You are a senior product manager who analyses the product videos.
        You will be provided with a video subtitles. 
        Use only the provided information to answer the user's questions.\n
        Question: {question} \nContext: {context} \nAnswer:
        """

    get_image_timestamp: str = """You are a senior product manager who analyses the product videos.
    You are provided with a set of video subtitles. and you need to find the timestamp of the image in the 
    video based on the provided description.
    Use only the provided information to answer the user's questions.\n
    Return only the timestamp of the image in the video as one number. \n
    Description: {description} \nAnswer:
    """

    get_image_name: str = """You are provided with a description for a requested image. 
    Return proper image name. It should ber shorter than 100 symbols, no spaced or special characters and without 
    extension. Return only the file name. \n
    Description: {description} \nAnswer:
    """

    assistant_description_prompt: str = """
    Create an assistant description based on provided documentation. It should be no more than 400 symbols.
    it should clearly describe with content of the documentation. Do not add any links to the sources. 
    """

    telegram_formatting: str = """
    You are given a text. Format it to your best judgement based on these rules: 
    <b>text</b> - Bold text, <i>text</i> - Italicize text, <u>text</u> - Underline text, 
    <s>text</s> - Strikethrough text, <code>text</code> - highlight part of a piece of code, 
    <tg-spoiler>text</tg-spoiler> - spoiler formatting that hides the selected text, 
    <a href="http://www.example.com/">text</a>	Creates a hyperlink to the selected text. 
    Do not change text content. 
    """
