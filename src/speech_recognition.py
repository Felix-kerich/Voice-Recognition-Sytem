# import os
# import azure.cognitiveservices.speech as speechsdk
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# def recognize_from_microphone():
#     # Load environment variables
#     speech_key = os.environ.get('SPEECH_KEY')
#     speech_region = os.environ.get('SPEECH_REGION')

#     # Check if the variables are loaded correctly
#     if not speech_key or not speech_region:
#         raise ValueError("SPEECH_KEY and/or SPEECH_REGION are not set in the environment variables.")

#     # Configure speech recognition
#     speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
#     speech_config.speech_recognition_language = "en-US"

#     audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
#     speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

#     print("Speak into your microphone.")
#     speech_recognition_result = speech_recognizer.recognize_once_async().get()

#     if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         print("Recognized: {}".format(speech_recognition_result.text))
#     elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
#         print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
#     elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
#         cancellation_details = speech_recognition_result.cancellation_details
#         print("Speech Recognition canceled: {}".format(cancellation_details.reason))
#         if cancellation_details.reason == speechsdk.CancellationReason.Error:
#             print("Error details: {}".format(cancellation_details.error_details))
#             print("Did you set the speech resource key and region values?")

# if __name__ == "__main__":
#     recognize_from_microphone()
# import os
# import azure.cognitiveservices.speech as speechsdk
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# def recognize_from_microphone():
#     # Load environment variables
#     speech_key = os.environ.get('SPEECH_KEY')
#     speech_region = os.environ.get('SPEECH_REGION')

#     # Check if the variables are loaded correctly
#     if not speech_key or not speech_region:
#         raise ValueError("SPEECH_KEY and/or SPEECH_REGION are not set in the environment variables.")

#     # Configure speech recognition
#     speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
#     speech_config.speech_recognition_language = "en-US"

#     audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
#     speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

#     print("Speak into your microphone.")
#     speech_recognition_result = speech_recognizer.recognize_once_async().get()

#     if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         print("Recognized: {}".format(speech_recognition_result.text))
#     elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
#         print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
#     elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
#         cancellation_details = speech_recognition_result.cancellation_details
#         print("Speech Recognition canceled: {}".format(cancellation_details.reason))
#         if cancellation_details.reason == speechsdk.CancellationReason.Error:
#             print("Error details: {}".format(cancellation_details.error_details))
#             print("Did you set the speech resource key and region values?")

# if __name__ == "__main__":
#     recognize_from_microphone()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.query_llm import process_input
from src.text_to_speech import talk
import logging
import asyncio
import json

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Flag to indicate if the LLM is busy processing a request
is_busy = False

@app.websocket("/ws/llm_response")
async def llm_response(websocket: WebSocket):
    global is_busy  # Use the global flag
    await websocket.accept()
    logging.info("WebSocket connection established.")

    try:
        while True:
            # Wait for the query
            query = await websocket.receive_text()
            logging.info(f"Received query: {query}")

            if is_busy:
                await websocket.send_text("System is busy processing another request. Please wait.")
                continue  # Wait for the next message

            # Set the flag to indicate LLM is processing
            is_busy = True

            try:
                # Process the input using the LLM (asynchronously)
                llm_response = await asyncio.to_thread(process_input, query)
                logging.info(f"LLM Response: {llm_response} | Type: {type(llm_response)}")

                # Prepare the response to send
                response_to_send = prepare_response(llm_response)
                logging.info(f"Response to send: {response_to_send}")

                # Log the response before talking
                logging.info("Speaking the response...")

                # Only speak the response without any transcription
                talk(response_to_send)

                # Optionally, send the response back to the client if needed
                # await websocket.send_text(response_to_send)
                logging.info("Response sent to client (if applicable).")

            finally:
                # Reset the flag when done
                is_busy = False

    except WebSocketDisconnect:
        logging.info("LLM response WebSocket disconnected.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await websocket.send_text("An error occurred while processing your request.")
    
    finally:
        # Ensure the WebSocket is closed properly
        await websocket.close()
        logging.info("WebSocket connection closed.")

def prepare_response(llm_response):
    """Prepare the response based on the LLM output."""
    if llm_response is None:
        logging.warning("LLM response is None, sending default message.")
        return "No response generated."
    
    if isinstance(llm_response, str):
        return llm_response
    elif isinstance(llm_response, (dict, list)):
        try:
            return json.dumps(llm_response)  # Convert to JSON string
        except TypeError as e:
            logging.error(f"JSON serialization error: {e}")
            return str(llm_response)  # Fallback to string
    else:
        return str(llm_response)  # Fallback to string conversion

if __name__ == "__main__":
    import uvicorn
    # Start the FastAPI server on localhost at port 8001
    uvicorn.run(app, host="127.0.0.1", port=8001)
