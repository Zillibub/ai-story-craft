from dataclasses import dataclass

@dataclass
class Formatter:
    """
    Can be used to format text in different ways.
    """

    telegram_formatting: str = """
        You are given a text. Format it based on these rules: 
        <b>text</b> - Bold text, <i>text</i> - Italicize text, <u>text</u> - Underline text, 
        <s>text</s> - Strikethrough text, <code>text</code> - highlight part of a piece of code, 
        <a href="http://www.example.com/">text</a>	Creates a hyperlink to the selected text. 
        
        Your reply should be no more than 4096 characters.
        Result should not contain any other formatting tags.
        Make all headers with bold formatting.
        
        Text: {text} \nAnswer:
    """

    discord_formatting: str = """
        You are given a text. Format it based on these rules:
        **text** - Bold text, *text* - Italicize text, __text__ - Underline text,
        ~~text~~ - Strikethrough text, `text` - highlight part of a piece of code
        
        Split the reply in chunks with maximum size of 2000 symbols.
        Slit the text logically, try not to break any big parts. 
        Return them as in json format as a list of strings.
        
        Text: {text} \nAnswer:
        """


@dataclass
class ProductManager:
    instructions: str = """You are a senior product manager who analyses the product videos.
        You will be provided with a video subtitles. 
        Use only the provided information to answer the user's questions.\n
        Question: {question} \nContext: {context} \nAnswer:
        """

    contextualize: str = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is. \n
        Question: {question} \nChat history: {history} \nAnswer:
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

    user_story_mapping: str = """
        You are a senior product manager who analyses the product videos. 
        You will be provided with a video subtitles with product description. 
        Create a user story map for the presented product. 
        Each task should have the following information: 
        1. Description. Provide actions, performed by the user. Write at least 2-3 sentences. 
        If there are any specific terms or definitions, try to add the to the description. 
        
        2. Goal. provide the reason for the action, 1-2 sentences.
        
        3. Reason. provide the benefit of the action, 1-2 sentences.
        
        Return only user story map. Use only provided information.  
        
        Video subtitles: {subtitles} \nAnswer:
    """

