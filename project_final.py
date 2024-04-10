import docx2txt
from PyPDF2 import PdfReader
import flask
from flask import Flask, render_template, request
import ast
import requests
import scipy, pandas as pd, numpy as np
import openai
from openai import OpenAI
from openai import AzureOpenAI
from werkzeug.utils import secure_filename
import json
import nltk
import tiktoken
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

load_dotenv()
prompt_token_limit = 3000
chunk_size = 2500
tokenizer = tiktoken.get_encoding('cl100k_base')
openai_api_key = "API_KEY"
bing_search_api_key = "BING"
bing_search_endpoint = "LINK"




introgative_pronuns = ["what","who","where","when","why","how","whose","which","whom","whosever","whichever","what's","who's","how's","when's"]
conjuctions = ["and","or","but","so","nor","yet","vs", "v/s", "versus"]

pronouns = ["this","that","these","those","that","they","their","it","there","its"]

app = Flask(__name__)

#topic analyzer
first_page1 = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Topic Extractor</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="get_relevancy" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Context</h1>
      <textarea id="ques" name="question_text" cols="80" rows="20" style="height:125px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">
'''
first_page2 = '''</textarea>
    <br> <br><br>
    <input type="file" name="file">
    <br> <br><br>

        <button type="submit" class="button">Analyze Topics</button>
    </form>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>
    <h1 style= "font-size:18pt;">Analyzed Topics</h1>
    '''
first_page3 = '''
    </body>
</html>
    '''
first_page = first_page1 + first_page2 + "<p> --- </p>" + first_page3
prompt_page1_req = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }


</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Extraction of  Requirements</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="extracted_req" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Requirements extraction</h1>
      <textarea id="ques" name="summary_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''

prompt_page2_req = '''</textarea>
    <br> <br><br>
    <input type="file" name="file">
    <br> <br><br>
        <button type="submit" class="button">Extract requirements</button>
'''
prompt_page3_req = '''
      <h1 style= "font-size:18pt;">Extracted requirements</h1>

      <textarea id="points" class="textbox" name="point_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">
'''
prompt_page4_req = '''
    </textarea>

    </form>
    <br><br>
    <form action='requirements'>
         <button type="submit" class="button">New</button>
      </form>
      <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>

   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }
        function removeSpaces(topicName) {
            return topicName.split(' ').join('');
            }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>


    '''
prompt_page5_req = '''
    </body>
</html>
    '''
prompt_page_req = prompt_page1_req + prompt_page2_req + prompt_page3_req + prompt_page4_req + prompt_page5_req

second_page1_cs = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Compute cosine score</h2>
  </div>
</body>
<body>
  <br><br><br>
  <br><br><br>
  <br><br><br>
  <br><br><br>

  <div  style = 'text-align: center'>
      <textarea id="ques" name="sentence" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''

second_page2_cs = '''</textarea>
      <br><br>
      <form action='find_cosine_score'>
         <button type="submit" class="button">New</button>
      </form>
     <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>
   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>


    '''
second_page5_cs = '''
    </body>
</html>
    '''
first_page1_main = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button-container {
      display: flex;
      justify-content: center;
      margin-top: 20px; /* Adjust as needed */
    }
.button {
      background-color: #00008B;
      border: none;
      color: white;
      padding: 13px 25px;
      text-align: center;
      text-decoration: none;
      display: inline-block;
      font-size: 14px;
      margin: 0 10px; /* Adjust as needed */
      transition-duration: 0.4s;
      cursor: pointer;
      border-radius: 25px;
    }
.button:hover {
      background-color: #000000;
    }
body {
      font-family: Arial;
    }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">RFP file processing system</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <br><br><br>
    <br><br><br>
    <form action="topic_analyzer" method="post" enctype="multipart/form-data">
             <button type="submit" class="button">Document analyzer</button>
    </form>
    <form action="requirements" method="post" enctype="multipart/form-data">
             <button type="submit" class="button">Extrat Key Terms</button>
    </form>
    <form action="prompt_context" method="post" enctype="multipart/form-data">
             <button type="submit" class="button">Get prompt context(IRI)</button>
    </form>
    <form action="bing_search" method="post" enctype="multipart/form-data">
             <button type="submit" class="button">Bing search</button>
    </form>
    <form action="get_answer" method="post" enctype="multipart/form-data">
             <button type="submit" class="button">Generate final response(Copy context from IRI/Bing search)</button>
    </form>
    <form action="intial_exec" method="post" enctype="multipart/form-data">
             <button type="submit" class="button">Executive summary</button>
    </form>
</body>
</html>'''

#executive summary
prompt_page1_exec = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }


</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Executive summary prompt refining(optional)</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="generate_prompt" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Executive Summary</h1>
      <textarea id="ques" name="summary_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''

prompt_page2_exec = '''</textarea>
    <br> <br><br>
    <input type="file" name="file">
    <br> <br><br>
    <button type="submit" class="button">Generate prompt</button>
'''
prompt_page3_exec='''
      <h1 style= "font-size:18pt;">Refined prompt</h1>

      <textarea id="points" class="textbox" name="point_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">
'''
prompt_page4_exec='''
    </textarea>
    </form>
    <form action="/pain_point_mainpage" method="post" enctype="multipart/form-data">
      <button type="submit" class="button">Next</button>
    </form>

   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }
        function removeSpaces(topicName) {
            return topicName.split(' ').join('');
            }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>


    '''
prompt_page5_exec= '''
    </body>
</html>
    '''
prompt_page_exec = prompt_page1_exec + prompt_page2_exec + prompt_page3_exec+prompt_page4_exec+prompt_page5_exec




first_page1_exec = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Client's name and pain points</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="find_pain_point" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">RFP</h1>
      <textarea id="ques" name="question_text" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''

first_page2_exec = '''</textarea>
    <br> <br><br>
    <input type="file" name="file">
    <br> <br><br>
    <button type="submit" class="button">Find client's name and pain points</button>
'''
first_page3_exec='''
      <h1 style= "font-size:18pt;">Identified Client's name and pain points</h1>

      <textarea id="points" class="textbox" name="point_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">
'''
first_page4_exec='''
    </textarea>
    </form>
    <form action="executive_summary" method="post" enctype="multipart/form-data">
      <button type="submit" class="button" >Next</button>
    </form>

   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>


    '''
first_page5_exec= '''
    </body>
</html>
    '''
first_page_exec = first_page1_exec + first_page2_exec + first_page3_exec+first_page4_exec+first_page5_exec


second_page_exec='''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Executive summary</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="final_executive_summary" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Client's name and pain points</h1>
      <textarea id="ques" name="pain_point_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''
second_page2_exec='''</textarea>
      <h1 style= "font-size:18pt;">Sample Executive summary</h1>
      <textarea id="ques" name="sample_summary_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">
'''
second_page3_exec='''
      </textarea>
      <h1 style= "font-size:18pt;">Information about the responding organization(default-Responsive)</h1>
      <textarea id="ques" name="org_info_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
second_page4_exec='''</textarea>
      <h1 style= "font-size:18pt;">Addtional instructions from user(optional)</h1>
      <textarea id="ques" name="user_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
second_page5_exec='''</textarea>
      <h1 style= "font-size:18pt;">Prompt</h1>
      <textarea id="prompt" name="prompt_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
second_page6_exec='''</textarea>
  <h1 style= "font-size:18pt;">Word limit(numbers only)</h1>
  <textarea id="limit_words" name="limit_words"  style="background-color:rgb(239, 239, 239);">'''
second_page7_exec='''</textarea>
     <br> <br><br>
    <label>
        <input type="radio" name="model" value="gpt-3.5-turbo-16k">
        GPT-3.5-turbo-16k
    </label>

    <label>
        <input type="radio" name="model" value="gpt-4">
        GPT-4
    </label>
     <br> <br><br>
    <button type="submit" class="button" >Generate executive summary</button>

  </form>
  <h1 style= "font-size:18pt;">Executive summary</h1>
  <textarea id="ques" name="user_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
second_page8_exec='''</textarea>
<form action='intial_exec'>
         <button type="submit" class="button">New</button>
      </form>
      <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>

      <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>
</body>
</html>


'''

#top10 and context html string
first_page1_top10 = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Top 10 and context</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="context" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Question</h1>
      <textarea id="ques" name="sentence" cols="80" rows="20" required style="height:50px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''
first_page11_top10 = '''</textarea> 
    <br>
    <button type="submit" class="button">Fetch</button>
'''
first_page2_top10 = '''
<br>
      <h1 style= "font-size:18pt;">Top 10 IRI results</h1>
      <textarea id="ques" name="Top10" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
first_page21_top10 = '''
      </textarea>
<br><br><br>
       <h1 style= "font-size:18pt;">Prompt context</h1>
      <textarea id="prompt" name="prompt" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
first_page22_top10 = '''
      </textarea>'''
first_page3_top10 = '''
    <br><br><br>
    '''
first_page4_top10 = '''
</form>
<br><br>
      <button type="submit" class="button" onclick="selectAllAndCopy()">Copy</button>
      <form action='prompt_context'>
         <button type="submit" class="button">New</button>
      </form>
      <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>
   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
        function selectAllAndCopy() {
            // Get the text area element
            var textArea = document.getElementById("prompt");

            // Select all the text in the text area
            textArea.select();

            // Copy the selected text to the clipboard
            document.execCommand('copy');

            document.getSelection().removeAllRanges();

        }
    </script>


    '''
first_page5_top10 = '''
    </body>
</html>
    '''
first_page_top10 = first_page1_top10 + first_page11_top10 +first_page3_top10

#bing_search html string
first_page1_search = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Bing search</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="result" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Question</h1>
      <textarea id="ques" name="question" cols="80" rows="20" required style="height:50px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''

first_page2_search = '''</textarea>
<br>
      <button type="submit" class="button">Search</button>
      </form>
'''
first_page21_search = '''
      <h1 style= "font-size:18pt;">Web search result</h1>
      <textarea id="ques2" name="list_sentence" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
first_page3_search = '''
      </textarea>
      <br>
      <button type="submit" class="button" onclick="selectAllAndCopy()">Copy</button>
      <h1 style= "font-size:18pt;">Final response</h1>
      <textarea id="ques2" name="list_sentence" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
first_page33_search='''</textarea>
<br><br>
      <form action='/bing_search'>
         <button type="submit" class="button">New</button>
      </form>
      <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>
   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });

        function selectAllAndCopy() {
            // Get the text area element
            var textArea = document.getElementById("ques2");

            // Select all the text in the text area
            textArea.select();

            // Copy the selected text to the clipboard
            document.execCommand('copy');

            document.getSelection().removeAllRanges();

        }
    </script>

</body>
</html>

    </script>


    '''
first_page5_search =  '''
    </body>
</html>
    '''
first_page_search = first_page1_search + first_page2_search +first_page5_search

#get answer html string
first_page1_get_answer = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }

</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Generate final response</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="model_answer" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Prompt</h1>
      <textarea id="ques" name="prompt" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">

'''

first_page2_get_answer = '''</textarea>
<br><br><br>
      <button type="submit" class="button">Get result</button>
      </form>
'''
first_page21_get_answer = '''
      <h1 style= "font-size:18pt;">Final result</h1>
      <textarea id="ques" name="list_sentence" cols="80" rows="20" required style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
first_page3_get_answer = '''
      </textarea>
<br><br><br>
      <form action='/get_answer'>
         <button type="get_answer" class="button">New</button>
      </form>
      <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>
<br><br><br>
   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>


    '''
first_page5_get_answer = '''
    </body>
</html>
    '''
first_page_get_answer = first_page1_get_answer + first_page2_get_answer +first_page5_get_answer

#compound_questions ui
prompt_page1 = '''
<html >
<head>
  <title>Responsive</title>
  <style>
.button {
  background-color: #00008B;
  border: none;
  color: white;
  padding: 13px 25px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 4px 2px;
  transition-duration: 0.4s;
  cursor: pointer;
  border-radius: 25px;
}
.button:hover {
  background-color: #000000;
  color: white;
}
body {
  font-family: Arial;
}
.split {
  height: 80%;
  width: 50%;
  position: fixed;
  z-index: 1;
  top: 15%;
  overflow-x: hidden;
  padding-top: 20px;
}
.left {
  left: 0;
  background-color: white;
}
.right {
  right: 0;
  background-color: white;
}
.centered {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.topcentered {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.vl {
  border-left: 3px solid black;
  height: 650px;
  position: absolute;
  left: 0%;
  margin-left: -1px;
  top: 1;
}
#number {
  width: 3em;
  height: 2em;
  margin-right: 35em;
}

.center-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }


</style>
</head>
<body>
  <div style= "background-color:#00008B; padding:10px">
    <h2 style="color:white;text-align:center;font-size:20pt">Generation of  Standalone questions from Compound question</h2>
  </div>
</body>
<body>
  <div  style = 'text-align: center'>
    <form action="generated_questions" method="post" enctype="multipart/form-data">
      <h1 style= "font-size:18pt;">Generate standalone questions</h1>
      <textarea id="ques" name="question" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''

prompt_page2 = '''</textarea>
    <br> <br><br>

    <br> <br><br>
        <button type="submit" class="button">Generate questions</button>
'''
prompt_page3 = '''
      <h1 style= "font-size:18pt;">Generated Standalone questions</h1>

      <textarea id="points" class="textbox" name="point_text" cols="80" rows="20" style="height:200px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">'''
prompt_page4 = '''</textarea>

    </form>
    <br><br>
    <form action='get_standalone_questions'>
         <button type="submit" class="button">New</button>
      </form>
    <br><br>
    <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>

   </div>
  </div>

    <script>
        // Function to create a new topic with close button
        function createTopic(topicName) {
            const topicContainer = document.getElementById("topicContainer");

            const topic = document.createElement("div");
            topic.classList.add("topic");

            const topicText = document.createElement("span");
            topicText.textContent = topicName;

            const closeIcon = document.createElement("span");
            closeIcon.innerHTML = "&#10006;";
            closeIcon.classList.add("close-icon");
            closeIcon.addEventListener("click", function() {
                topicContainer.removeChild(topic);
            });

            topic.appendChild(topicText);
            topic.appendChild(closeIcon);

            topicContainer.appendChild(topic);

            // Append the topic name to the form data
            const topicInput = document.createElement("input");
            topicInput.type = "hidden";
            topicInput.name = "topicInput"; // Set the name attribute to "topicInput"
            topicInput.value = topicName;
            topic.appendChild(topicInput);
        }
        function removeSpaces(topicName) {
            return topicName.split(' ').join('');
            }

        // Function to handle adding topics on "Add" button click
        document.getElementById("addTopicBtn").addEventListener("click", function(event) {
            event.preventDefault(); // Prevent form submission

            const newTopicName = document.getElementById("newTopicInput").value.trim();
            if (newTopicName) {
                createTopic(newTopicName);
                document.getElementById("newTopicInput").value = "";
            }
        });
    </script>


    '''
prompt_page5 = '''
    </body>
</html>
    '''
prompt_page = prompt_page1 + prompt_page2 + prompt_page3 + prompt_page4 + prompt_page5


def openai(prompt):

  completion = OpenAI(api_key = "").chat.completions.create(model = "gpt-3.5-turbo-0125", temperature = 0,
                                                    messages = [{"role": "system", "content": "You are a responsible and ethical organization"}, {"role": "user", "content": prompt}])

  model_answer=completion.choices[0].message.content
  return model_answer
  

def classify(question):
    try:
        split_char_count = question.count("?") + question.count(".")
        split_char_count2 = question.count("\n") + question.count(",") + question.count(";") +question.count("/")
        if split_char_count >= 2 or split_char_count2 > 0:
            result = "Yes"

        else:
            cleaned_question = re.sub(r'[?.;,]', '', question)
            counts = {element: cleaned_question.lower().split().count(element) for element in introgative_pronuns}
            total_count = sum(counts.values())
            if total_count > 0:
                result = "Yes"

            else:

                conj_counts = {element: cleaned_question.lower().split().count(element) for element in conjuctions}
                conj_counts["as well as"] = 1 if "as well as" in cleaned_question else 0
                print(conj_counts)
                total_conj_count = sum(conj_counts.values())
                if total_conj_count > 0:
                    result = "Yes"

                else:
                    all_pronoun = conjuctions + pronouns
                    pro_counts = {element: cleaned_question.lower().split().count(element) for element in all_pronoun}
                    pro_counts["as well as"] = 1 if "as well as" in cleaned_question else 0
                    total_pro_count = sum(pro_counts.values())
                    if total_pro_count >= 2:
                        result = "Yes"
                    else:
                        result = "No"
        return result
    except Exception as ex:
        raise ex

         
@app.route('/get_standalone_questions', methods=['GET', 'POST'])
def hello():
    return prompt_page

@app.route('/generated_questions', methods=['GET', 'POST'])
def main():
	question = request.form.get('question').strip()
	classification_result = classify(question)
	if classification_result == "Yes":
		prompt = "Compounded multiple question: \nAre staff have trained to access and process customer personal information ;and are required to maintain the confidentiality and security of that data?\nIndividual standalone questions: \n1. Are staff have trained to access and process customer personal information?\n2. Are staff members required to maintain the confidentiality and security of customer data?\n\nCompounded multiple question: \nWhat technical guidance do you provide to your customers about vulnerabilities, including how they could be exploited, how they are currently being exploited, and how to mitigate?\nIndividual standalone questions: \n1. What technical guidance do you provide to your customers about vulnerabilities?\n2. How do you inform your customers about the current methods of exploitation for vulnerabilities?\n3. What strategies do you recommend to your customers for mitigating vulnerabilities in their systems?\n\nCompounded multiple question: \nDo you have an easily discoverable way for external parties to report security vulnerabilities?\nDo you use have  any automation tools for that?\nIndividual standalone questions: \n1. Do you have an easily discoverable way for external parties to report security vulnerabilities?\n2. Do you use any automation tools for managing and tracking reported security vulnerabilities?\n\nCompounded multiple question: \nWhat factors contribute to the development of sustainable urban environments and how do these considerations affect long-term city planning and infrastructure design?\nIndividual standalone questions: \n1. What factors contribute to the development of sustainable urban environments?\n2. 2. How do considerations for sustainable urban environments affect long-term city planning and infrastructure design?\n\nInstructions:\n-Please follow the steps below to generate Individual standalone questions from given Compounded multiple question.f the question does not looks like Compounded multiple question, then return original question itself.\n-Break down the given Compounded multiple question into individual questions\n-Generate Individual standalone questions from the above break down questions.\n-The generated Individual standalone questions should be an independent ,meaningful and should be complete by itself.\n-Replace the all pronouns with actual nouns in the final generated individual standalone questions.\n-Return only Individual standalone questions as response without post or pre-text.\n\nCompounded multiple question:\n"+question+"\nIndividual standalone questions: "
		print(prompt)
		comp_questions = openai(prompt)
		return prompt_page1 + str(question) + prompt_page2 + prompt_page3 + str(comp_questions) + prompt_page4 + prompt_page5
	else:
		return prompt_page1 + str(question) + prompt_page2 + prompt_page3 + str(question) + prompt_page4 + prompt_page5
	

def search(query):

    params = {'q': query}
    headers = {'Ocp-Apim-Subscription-Key': bing_search_api_key}

    try:
        response = requests.get(bing_search_endpoint,
                                headers=headers, params=params)
        response.raise_for_status()
        json_val = response.json()
        return json_val["webPages"]["value"]
    except Exception as ex:
        raise ex



def bing_search_result(question):
    try:
        # ip_data = request.get_json()
        results = search(question)
        results_prompts = [f"Source:\nTitle: {result['name']}\nURL: {result['url']}\nContent: {result['snippet']}" for result in results]
        prompt = "Use the following sources to answer the question:\n\n" + "\n\n".join(results_prompts) + "\n\nQuestion: " + question + "\n\nAnswer:"
        if results:
            response = OpenAI(api_key=openai_api_key).chat.completions.create(model='gpt-4-0125-preview',
                                                                              messages=[{"role": "user", "content": prompt}])

            answer = response.choices[0].message.content.strip(" \n")
            url_links = [result['url'] for result in results]
            print("p",prompt)
            return {'web_search_result':prompt,'response': answer}
        else:
            return {'web_search_result':"","response":"",'error': 'Search could not fetch results for the given question. Try a different question.'}
    except Exception as e:
        error_info = "Exception occurred: " + str(e)
        return {"error": error_info}


def jaccard_similarity(text1, text2):
    try:
        tokens1 = set(nltk.word_tokenize(text1.lower()))
        tokens2 = set(nltk.word_tokenize(text2.lower()))

        # Calculate Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        similarity = intersection / union
        return similarity
    except Exception as e:
        error_info = "Exception in jaccard_similarity function: " + str(e)
        return 0

def update_emb_results(emb_results, query):
    try:
        query = query.lower()
        for emb_result in emb_results:
            emb_result_text = emb_result["text"].lower()
            cosine_score = float(emb_result["score"])
            jacc_score = jaccard_similarity(query, emb_result_text)
            update_score = (0.9 * cosine_score) + (0.1 * jacc_score)
            emb_result["score"] = update_score
        emb_results = sorted(emb_results, key=lambda key: key["score"], reverse=True)
        return emb_results
    except Exception as e:
        error_info = "Exception in update_emb_results function: " + str(e)
        return emb_results

def create_chunks(prompt, chunk_size, top_n=None):
    try:
        logger_list = {"message": ""}
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0,
                                                       length_function=token_len, separators=[".", "!", "?", ";", "\n"])
        chunks = text_splitter.split_text(prompt)
        if top_n:
            return "".join(chunks[:top_n])  # to get top n chunks
        else:
            return chunks
    except Exception as e:
        error_info = "Exception while creating the chunks: " + str(e)
        return ""

def token_len(prompt):
    try:
        logger_list = {"message": ""}
        tokens = tokenizer.encode(prompt, disallowed_special=())  # token length
        return len(tokens)
    except Exception as e:
        error_info = "Exception while finding the token length: " + str(e)
        return 0

def post_process_chunks(prompt_contxt):
    try:
        logger_list = {"message": ""}
        last_ques_pos = prompt_contxt.rfind("\nQ: ")
        last_ques = prompt_contxt[last_ques_pos:]
        if "\nA: " in last_ques:
            pass
        else:
            prompt_contxt = prompt_contxt[:last_ques_pos]
        return prompt_contxt
    except Exception as e:
        error_info = "Exception in post_process_chunks function: " + str(e)

        return prompt_contxt

def context(ip):

            emb_results = ip["embeddingResults"] if "embeddingResults" in ip else []
            query = ip["query"]
            context = ip["context"] if "context" in ip else {}
            final_context = []
            top_score = float(emb_results[0]["score"])

            # update the emb_results with the combination jaccard and cosine_score
            if top_score < 0.90:
                emb_results = update_emb_results(emb_results, query["question"])
                top_score = float(emb_results[0]["score"])

            valid_thr = max(0, top_score - 0.10)

            # filter the embeddingResult and consider based on valid threshold. (not less than the 0.10 difference from top score)
            emb_results = [emb_result for emb_result in emb_results if float(emb_result["score"]) > valid_thr]

            for emb_result in emb_results:
                id_type = emb_result.get("type", "CONTENTS")
                if id_type == "TITLE" or id_type == "ALTERNATE_TITLES":
                    doc_id = emb_result["docId"]
                    context = ip["context"]
                    final_context.append(context[doc_id])
                elif id_type == "CONTENTS":
                    context = {"answers": [{"value": emb_result["text"]}]}
                    final_context.append(context)
                else:
                    pass
            result = {}
            cmd = "Answer the Query using only the above information. If not sure about the answer reply as **Don't Know**."
            instruction = " The response should follow the User instructions. User instructions: "
            context_answers = "".join(["\n\nQ: " + pairs["question"] + "\nA: " + answer["value"] if "question" in pairs \
                                           else "\n\nA: " + answer["value"] for pairs in final_context for answer in
                                       pairs["answers"]])
            pq = "\n\n\nQuery: " + query["question"] + "\nAnswer:"

            context_token_limit = prompt_token_limit - token_len(cmd + pq)  # caculate the token limit of context
            context_answers = create_chunks(context_answers, context_token_limit, 1)  # get the first chunks of context
            context_answers = post_process_chunks(context_answers)
            prompt = context_answers + pq + "\n\n\n" + cmd

            if context_answers == "":  # if the context is empty stop the process and return {}
                error_info = "No context provided"
                return {"Response": "", "error": error_info}
            return prompt


def find_cosine_score(emb1, emb2, output="one"):
    cosine_scores = 1 - scipy.spatial.distance.cdist(emb1, emb2, "cosine")[0]
    cosine_scores = list(map(lambda score: min(1.0, max(0.0, score)), cosine_scores))
    if output == "one":
        return cosine_scores[0]
    else:
        return cosine_scores

def get_embedding(text, model):
    if model.strip() in ["text-embedding-ada-002", "text-embedding-3-large", "text-embedding-3-small"]:
        output = OpenAI(api_key="").embeddings.create(input=text, model=model).data[0].embedding
        return output
    else:
        if model.strip()== "dev1-embedding":
            print(model)
            output = AzureOpenAI(api_version="", azure_endpoint="", api_key="").embeddings.create(input=text, model=model).data[0].embedding
        else:
            output = AzureOpenAI(api_version="", azure_endpoint="", api_key="").embeddings.create(input=text, model=model).data[0].embedding
        return output
	
   	

def read_pdf(file_name):
    try:
        reader = PdfReader(file_name)
        text = ''
        for page_no in range(len(reader.pages)):
            text += reader.pages[page_no].extract_text()
        if text != "":
            return text
        else:
            return ""
    except Exception as e:
        error_info = "Exception in read_pdf function: " + str(e)
        return ""


def read_word(file_name):
    try:
        text = docx2txt.process(file_name)
        # text= json.loads(text)
        return text
    except Exception as e:
        error_info = "Exception in read_word function: " + str(e)
        return ""


def read_csv_files(file_name):
    try:
        text = pd.read_csv(file_name)
        text = text.fillna("")
        text = "\n\n".join(text.apply(lambda row: '|'.join(map(str, row)), axis=1).values)
        return text
    except Exception as e:
        error_info = "Exception in read_csv function: " + str(e)
        return ""


def get_content(files):
    try:
        content = ""
        file_name = files.filename

        if file_name.lower().strip().endswith(".pdf"):
            content = read_pdf(files)

        elif file_name.lower().strip().endswith(".docx"):
            content = read_word(files)

        elif file_name.lower().strip().endswith(".txt"):
            content = str(files.read())

        elif file_name.lower().strip().endswith(".csv"):
            print("came to csv")
            content = read_csv_files(files)
            # print(content)

        else:
            pass
        return content
    except Exception as e:
        error_info = "Exception in get_content function: " + str(e)
        return ""


def token_len(prompt):
    try:
        logger_list = {"message": ""}
        tokens = tokenizer.encode(prompt, disallowed_special=())  # token length
        return len(tokens)
    except Exception as e:
        error_info = "Exception while finding the token length: " + str(e)
        print(error_info)
        return 0


def create_chunks(context, chunk_size, top_n=None):
    try:
        logger_list = {"message": ""}
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0,
                                                       length_function=token_len, separators=[".", "!", "?", ";", "\n"])
        chunks = text_splitter.split_text(context)
        if top_n:
            return "".join(chunks[:top_n])  # to get top n chunks
        else:
            return chunks
    except Exception as e:
        error_info = "Exception while creating the chunks: " + str(e)
        print(error_info)
        return ""


def gpt_prompt(prompt):
    try:
       

        response = AzureOpenAI(api_version=AZURE_CHAT_APIVER, azure_endpoint=AZURE_CHAT_URL,
                               api_key=AZURE_CHAT_APIKEY).chat.completions.create(max_tokens=None,
                                                                                  model=AZURE_CHAT_MODEL,
                                                                                  temperature=0,
                                                                                  messages=[{"role": "system",
                                                                                             "content": "system_assistant"},
                                                                                            {"role": "user",
                                                                                             "content": prompt}])
        model_result = response.choices[0].message.content.strip(" \n")

        # print(round(time.time()-start,4))
        return model_result
    except Exception as e:
        error_info = "Exception while using the openai API: " + str(e)
        if "please reduce the length of the messages" in str(e).lower():
            message = "Exceeded models processing limit. Try reducing the size of input content."
        else:
            message = "Facing issue in GPT. Try again"

        return "", e



@app.route('/requirements', methods=['GET', 'POST'])
def requirements():
    return prompt_page_req


@app.route('/extracted_req', methods=['GET', 'POST'])
def extracted_req():
    try:

        files = request.files['file']
        print(files)
        text = get_content(files)
        prompt1 = "\n\nPlease identify and provide the following details from the provided input text:\n- Summary: Generate a brief summary consisting of 2-3 sentences for the given input text.\n- Requirements: Get all the Key Requirements from the input text.\n- Client's name: Find and return the client's name or client's company name from the given input text.\n- Project name: Find and return the name of the project from the given input text.\n- Due date: Find and return the Deadline or due date from the given input text.\n- Project value: Find and the project value or financial investment for the project mentioned in input text.\nreturn the response in json format."
        prompt2 = "\n\nPlease identify and provide the following details from the provided input text:\n- Requirements: Get all the Key Requirements from the input text.\n- Client's name: Find and return the client's name or client's company name from the given input text.\n- Project name: Find and return the name of the project from the given input text.\n- Due date: Find and return the Deadline or due date from the given input text.\n- Project value: Find and return the project value or financial investment for the project mentioned in input text.\nreturn the response in json format."

	
        final_model_result={}
        if token_len(text) < 10000:
            model_result = gpt_prompt("input text"+text + prompt1)
            model_result = json.loads(model_result)
            final_model_result["Summary"] = str(model_result["Summary"])

            final_model_result["Requirements"]  = str(model_result["Requirements"]).strip('[').strip(']')
            if "not" not in str(model_result["Client's name"]).lower():
                final_model_result["Client's name"] = str(model_result["Client's name"])
            else:
                final_model_result["Client's name"] = "Not provided"
            if "not" not in str(model_result["Project name"]).lower():
                final_model_result["Project name"] = str(model_result["Project name"])
            else:
                final_model_result["Project name"] = "Not provided"
            if "not" not in str(model_result["Due date"]).lower():
                final_model_result["Due date"] = str(model_result["Due date"])
            else:
                final_model_result["Due date"] = "Not provided"
            if "not" not in str(model_result["Project value"]).lower():
                final_model_result["Project value"] = str(model_result["Project value"])
            else:
                final_model_result["Project value"] = "Not provided"
            print("m", model_result)

            final_model_result = {key: value.lstrip(",") for key, value in final_model_result.items()}

        else:
            chunks = create_chunks(text, 10000)
            len(chunks)
            for i, j in enumerate(chunks):
                if i == 0:
                    prompt = "input text"+j + prompt1

                    final_model_result["Summary"] =""
                    final_model_result["Requirements"] =""
                    final_model_result["Client's name"] =""
                    final_model_result["Project name"] =""
                    final_model_result["Due date"] =""
                    final_model_result["Project value"] =""
                else:
                    prompt = "input text"+j + prompt2
                model_result = gpt_prompt(prompt)
                model_result = json.loads(model_result)
                if i ==0:
                    final_model_result["Summary"] += ","+str(model_result["Summary"])

                final_model_result["Requirements"] += ","+str(model_result["Requirements"]).strip('[').strip(']')
                if str(model_result["Client's name"]) not in final_model_result["Client's name"] and "not" not in str(model_result["Client's name"]).lower():
                    final_model_result["Client's name"] += ","+str(model_result["Client's name"])
                else:
                    final_model_result["Client's name"] = "Not provided"
                if str(model_result["Project name"]) not in final_model_result["Project name"] and "not" not in str(model_result["Project name"]).lower():
                    final_model_result["Project name"] += ","+str(model_result["Project name"])
                else:
                    final_model_result["Project name"] = "Not provided"
                if str(model_result["Due date"]) not in final_model_result["Due date"] and "not" not in str(model_result["Due date"]).lower():
                    final_model_result["Due date"] += ","+str(model_result["Due date"])
                else:
               	    final_model_result["Due date"] = "Not provided"
                if str(model_result["Project value"]) not in final_model_result["Project value"] and "not" not in str(model_result["Project value"]).lower():
                    final_model_result["Project value"] += ","+str(model_result["Project value"])
                else:
                	final_model_result["Project value"] = "Not provided"
                print("m", model_result)

                final_model_result = {key: value.lstrip(",") for key, value in final_model_result.items()}
        final_result = "Summary:\n"+final_model_result["Summary"]+"\n\nKey Requirements:\n"+final_model_result["Requirements"]+"\n\nClient's name:\n"+final_model_result["Client's name"]+"\n\nProject name:\n"+ final_model_result["Project name"] +"\n\nDue date\n"+final_model_result["Due date"]+"\n\nProject value:\n"+final_model_result["Project value"]

        return prompt_page1_req + str(text) + prompt_page2_req + prompt_page3_req + str(final_result) + prompt_page4_req + prompt_page5
    except Exception as e:
        error_info = "Exception in main: " + str(e)
        print(error_info)
        return 0
        

def openai_summary(prompt,model,system_assistant):

  from openai import OpenAI

  completion = OpenAI(api_key = "").chat.completions.create(model = model, temperature = 0,
                                                    messages = [{"role": "system", "content": system_assistant}, {"role": "user", "content": prompt}])

  extracted_pain_points=completion.choices[0].message.content
  return extracted_pain_points

@app.route('/model_answer',methods=["POST","GET"])
def model_answer():
  prompt= request.form.get("prompt")
  result=openai(prompt)
  return first_page1_get_answer + prompt+first_page2_get_answer + first_page21_get_answer + result+first_page3_get_answer + first_page5_get_answer
  


#get answer main function
@app.route('/get_answer',methods=["POST","GET"])
def get_answer():
  return first_page1_get_answer + first_page2_get_answer


@app.route('/result',methods=["POST","GET"])
def search_result():
  question=request.form.get("question")
  result=bing_search_result(question)
  print("result",result)
  return first_page1_search + question + first_page2_search + first_page21_search + str(result['web_search_result']) + first_page3_search + str(result['response']) + first_page33_search + first_page5_search

#bing_search main function
@app.route('/bing_search',methods=["POST","GET"])
def main_page_search():
  return first_page1_search + first_page2_search


@app.route('/context',methods=["POST","GET"])
def final_context():
  top_list=[]
  sentence=request.form.get('sentence').strip()

  url = 'https://qrelease.rfpio.com/rfpserver/ext/v1/content-lib/knn-search-input'
  headers = {
      'Authorization': 'Bearer a-b1fa57a80e6ee34567c0a9f82959a515',
      'Content-Type': 'application/json'
  }
  payload = {
      "title": sentence,
      "contents": [
          "Response"
      ],
      "questionId": "659fbcc432580c68217f95ad",
      "sectionId": "659fbcb032580c68217f954b",
      "projectId": "659fbca032580c68217f952e",
      "debug": False,
      "userInstruction": "",
      "operation": "First Draft",
      "companyDescription": "",
      "companyName": "Responsive Ask",
      "collectionList": [],
      "tags": [],
      "customFields": {
          "language": []
      },
      "language": "",
      "mergeTags": []
  }
  response = requests.post(url, headers=headers, json=payload)
  if response.status_code == 200:
      json_response = response.json()
  else:
      print("Error:", response.status_code)
      print(response.text)
  input = json_response
  emb_results=input["embeddingResults"]
  for num,i in enumerate(emb_results):
    emb_results_ques=i['text']
    emb_results_score=i['score']
    top_list.append([num+1,emb_results_ques,emb_results_score])
  final_context=context(input)
  return first_page1_top10 + sentence + first_page11_top10 + first_page3_top10 + first_page2_top10 + ('\n'.join(map(str, top_list)))+first_page21_top10 + str(final_context)+first_page22_top10 + first_page4_top10 + first_page5_top10


@app.route("/pain_point_mainpage",methods=["POST","GET"])
def index_pain():
    return first_page_exec

@app.route("/find_pain_point", methods=["POST","GET"])
def pain_point():
    try:
      topics = []
      context = request.form['question_text']
      topics = request.form.getlist('topicInput')

      # read the file, if the content is empty
      if context.strip() == "" and request.method == 'POST':
            files = request.files['file']
            filename = secure_filename(files.filename)
            print("fffff",filename)
            files.save(filename)
            context = get_content(files)

     

      print(type(context))
      print("total_context_len",token_len(context))
      if token_len(context)>16000:
          print("context_length:",token_len(context))
          chunk=create_chunks(context,6500)
          pain_points=""
          for chunked_context in chunk:
              pain_point_prompt=f"""
              ```````````````````````````````````
              Request For Proposal : {chunked_context}

              ````````````````````````````````````
              Find the client's name and identify the client's key pain points or challenges mentioned in the Request For Proposal.Express those key pain points in bulletin format"""
              output_pain_points=openai_summary(pain_point_prompt,'gpt-3.5-turbo-16k',"")
              pain_points+=output_pain_points
          print("pain_points_1:",pain_points)

      else:
            pain_point_prompt=f"""
              ```````````````````````````````````
              Request For Proposal : {context}

              ````````````````````````````````````
              Find the client's name and identify the client's key pain points or challenges mentioned in the Request For Proposal.Express those key pain points in bulletin format"""
            pain_points=openai_summary(pain_point_prompt,'gpt-3.5-turbo-16k',"")
            print("pain_points_2:",pain_points)
      file_path = "pain_points.txt"

      with open(file_path, 'w') as file:
        file.write(pain_points)

      result_page = first_page1_exec + context + first_page2_exec + first_page3_exec +pain_points+first_page4_exec+first_page5_exec
      return result_page
    except Exception as e:
      print(e)
      return first_page_exec


@app.route("/executive_summary", methods=["POST","GET"])
def executive_summary():
  with open('pain_points.txt', 'r') as file:
    # Read the content of the file
    pain_points_data= file.read()
  client_pain_points= pain_points_data
  User_instructions=""
  word_limit=""
  system_assistant= '''
            Responsive (formerly RFPIO, Inc.) is a privately owned developer of cloud-based software that automates and streamlines the process of responding to a request for proposal (RFP) based in Beaverton, Oregon. The company also maintains an office in Coimbatore, India.Founded in 2015, the company has expanded rapidly and now has more than 150,000 users worldwide after tripling its user base in 2019 and sustaining growth during the global pandemic. RFPIO software has supported more than $20 billion in RFP responses.

            History
            Original RFPIO Logo
            The company was founded as RFPIO in 2015 by Ganesh Shankar, AJ Sunder, and Sankar Lagudu to streamline RFP processes for mid-to-large enterprises.[7] RFPIO was formed in response to the problems Shankar and his colleagues experienced gathering information and compiling responses for RFPs and being unable to find a suitable automation solution. By developing a cloud-based proposal management system, Shankar aimed to simplify and automate the RFP process and make it easier for cross-functional teams to collaborate.

            The company experienced rapid growth from the outset and reported having 50 employees in Oregon and India at the end of 2018.

            On 2 October 2018, the company obtained its first patent involving the conversion and presentation of proposal documents in a user-friendly format. US patent 10089285, "Method to automatically convert proposal documents"

            In February 2019, Express Scripts selected the RFPIO response management platform as part of a long-term business transformation initiative. RFPIO reported over 250% growth and more than 125 employees by the end of 2019.

            In January 2020, RFPIO expanded its executive team with the additions of Angela Earl, vice president of global marketing and Mohan Natraj, vice president of customer success. Konnor Martin was also promoted to regional vice president of sales for North America. In July 2020, the company reported a 150% increase in usage of RFPIO services, continuing the firm's growth despite the COVID-19 pandemic.

            In April 2021, Microsoft reported saving an estimated $2.4M with RFPIO's Response Management Software. 18 months after implementation, the Microsoft team gave nearly 7,000 users access to 36,200 ready-to-go RFx responses from RFPIO's AI-enabled Answer Library, translating into 12,000 total hours saved.
            In August 2021, RFPIO acquired RFP360, a Kansas-based RFP software competitor, bringing RFPIO's employee count to 300.
            In July 2023, RFPIO changed its company name to Responsive.

            Financing
            RFPIO's first round of funding was secured in 2016 through Portland-based investment firm Elevate Capital and from the angel investment group TiE Oregon.[16] In October 2016, RFPIO received $100,000 at the Bend Venture Conference for the company's performance in the Growth Stage competition. In December 2016, Stephen Marsh, founder of Smarsh, whose company was an early customer of RFPIO, invested $500,000 in the company through his investment vehicle Archivist Capital.

            In July 2018, the company secured a $25 million funding round from private equity firm K1 Investment Management to accelerate growth and cashed out some of its early investors. This resulted in an early exit for Elevate Capital and produced significant returns.

            Services
            RFPIO's cloud-based software incorporates artificial intelligence, project management and collaboration capabilities and integrates with common sales management applications to help companies respond to RFPs. The platform also allows salespeople to create personalized, proactive selling documents and has built in e-signature functionality. Companies using RFPIO include ADP, Adobe, Britannica Digital Learning, Broadcom, DTI Global, Express Scripts, Google Cloud, Facebook, LinkedIn, Microsoft, Salesforce, Smarsh, Zoom and others from across multiple industry segments

            Awards and recognition
            In 2020, RFPIO was ranked 14th in a list of the top 100 software products for 2020 out of the more than 57,000 software companies listed on G2 Crowd, a crowd-sourced software review service.The company also received a Silver Stevie Award for Customer Service Department of the year, was named a top 10 tech startup in Oregon by The Tech Tribune, and listed 7th on a list of fastest-growing companies in Portland, Ore. by Growjo.The company received the award for Best Project Management Cloud Service in the 2019-20 Cloud Awards.CEO Ganesh Shankar won the EY Entrepreneur Of The Year 2020 Pacific Northwest Region Award and was listed 5th in Comparably's list of top CEOs for diversity.RFPIO was also named to Comparably lists for Top 50 Best Companies for Work-Life Balance, Top 50 Happiest Employees, and Top 50 Best Perks & Benefits.In August 2022, RFPIO's HR Shipra Kamra was featured on the front cover of the Portland Business Journal and was also featured on Women's We Admire list of Top 50 Women Leaders of Oregon.
            '''

  sample_executive_summary='''
                May 2, 2023
                City of Oshawa
                City Hall
                50 Centre Street South
                Oshawa, Ontario L1H 3Z7
                RE: C2023-034
                Ritson Road North & Columbus Road East (Roundabout) Design
                MTE Consultants is excited about this project. Since 2004, we have been actively developing a specialization
                in the engineering design and construction of roundabouts. We attribute our success with roundabouts to our
                experience in municipal engineering, our approach to project management and public consultation, the technical
                expertise of our team members, and the range of additional services that we offer.
                MTE plays a significant role in the development of the policy and practices regarding the use of modern
                roundabouts for major intersections in the Southwestern Ontario area. We have trained our designers with
                Arcady Software and are members of the International Roundabout Consortium through the Transport Research
                Board (TRB). We have attended numerous conferences and training seminars and along with our design and
                construction experience, we feel very confident in our ability to execute successful roundabout projects from
                rural to urban, low to high speed, high volume.
                Through our involvement in the Ira Needles Boulevard project which included five MTE-designed roundabouts,
                the double-roundabout at Ottawa Street/Homer Watson Boulevard and Ottawa Street/Alpine Road, as well as
                several other roundabout projects, we have developed a strong background in the design and construction of
                modern roundabouts.
                MTE has now successfully completed the design and/or construction of more than 25 roundabouts in the
                Waterloo Region and the surrounding area. We know what it takes to get the job done. The overall construction
                value for MTE completed roundabout projects totals over $50 million.
                We have modified and improved seemingly minor details during the design process that have resulted in better
                functionality of the intersections. We have improved our roundabout grading processes and learned from
                previous construction projects where our attention is most important in the design development. A solid design
                solution and careful consideration of efficient and safe construction staging will result in successful project
                execution. The project being proposed by the City of Oshawa is a not a standard roundabout, and will feature
                complicated geometry. We believe that this project should be completed by a firm that has demonstrated that it
                can be relied upon to provide a design for a safe and functional roundabout, and we are sincerely excited about
                the opportunity to demonstrate that we have the expertise the City is looking for.
                Sincerely,
                MTE Consultants Inc.

                Dot Roga, C.E.T.
                Manager, Municipal Engineering
                519-743-6500 Ext. 1269
                DRoga@mte85.com'''
  with open('prompt.txt', 'r') as file:
    # Read the content of the file
            part_Prompt= file.read()
    


    
      
  return second_page_exec+client_pain_points+second_page2_exec+sample_executive_summary+second_page3_exec+system_assistant+second_page4_exec+second_page5_exec+part_Prompt+second_page6_exec+second_page7_exec+second_page8_exec
@app.route("/final_executive_summary", methods=["POST","GET"])
def final_executive_summary():
  try:
      client_pain_points= request.form.get('pain_point_text')
      sample_executive_summary=request.form.get('sample_summary_text')
      system_assistant=request.form.get('org_info_text')
      User_instructions=request.form.get('user_text') if request.form.get('user_text') else ""
      model = request.form.get('model') if request.form.get('model') else "gpt-3.5-turbo-16k"
      part_Prompt=request.form.get('prompt_text')
      word_limit=request.form.get('limit_words')
      print("word_limit",word_limit)
            
      with open('prompt.txt', 'r') as file:
    # Read the content of the file
            part_Prompt= file.read()
      
      Prompt=f'''
        ```````````````````````````````````
        Request For Proposal : {client_pain_points}
        User instructions :{User_instructions}
        sample executive summary: {sample_executive_summary}
        ````````````````````````````````````
        {part_Prompt}      
        If User instructions or sample executive summary or word limit is detected, proceed with the following instructions; otherwise, return the output from the previous prompt.
          Ensure to incorporate User instructions while crafting the executive summary.
          Utilize the provided sample executive summary solely as a reference for crafting an engaging and effective executive summary.
          Please rewrite the above generated executive summary in approximately {word_limit} words
                  '''

      executive_summary=openai_summary(Prompt,model,system_assistant)
      print(User_instructions)
      print("ee",executive_summary)
      result=second_page_exec+client_pain_points+second_page2_exec+sample_executive_summary+second_page3_exec+system_assistant+second_page4_exec+ User_instructions+second_page5_exec+part_Prompt+second_page6_exec+word_limit+second_page7_exec+executive_summary+second_page8_exec
      return result
  except Exception as e:
      print(e)
      return first_page_exec



@app.route("/generate_prompt",methods=["POST","GET"])
def generate_prompt():
  sample_executive_summary=request.form.get("summary_text")
  print(sample_executive_summary)
  default_prompt="""
    Crafting an engaging executive summary for the Request For Proposal that should incorporates the provided templates and points:
    At start of the executive summary,
      Dear [Client's Name],
      Provide complete overview about the company.
      Mention about the solution and features offered by the company.
      Add information about How AI has be incorporated in our solution

    Middle portion of the executive summary,
      Start by briefly describing the client's key pain points or challenges to demonstrate your understanding of their needs.
      Provide a basic overview of the proposed solution.
      Explain how the company's unique strengths and capabilities effectively address and resolve these challenges.
      Mention what sets the company apart from the competition to stimulate the client's interest.
      Conclude the introduction with a positive and emotionally resonant message to leave the client excited about the potential benefits the company can offer.

      Additionally, the summary should include the following elements:
        Offer an overview of the document's contents, showcasing key successes, client stories, or standout features that differentiate the company.
        Summarize the benefits the client will derive from the solution provided by the company, using a clear and concise bullet point format.
        Highlight the company's key qualifications, with an emphasis on the years of experience and substantial cost savings achieved for previous customers.
        Mention any extra value-added benefits that the company provides.

    At the conclusion of the executive summary,
      Add information about why you are better than any other company in this domain.
      Highlight the points that why they need us for their problem.
      The goal is to create an summary that informs, engages, and motivates the client to explore the full Request for Proposal.
      When crafting the executive summary, assign more importance to avoiding phrases like 'In summary' or 'In conclusion' to enhance its engagement and effectiveness.

    """
  main_prompt=f"""
    ----------------------------
    summary:{sample_executive_summary}
    prompt:{default_prompt}
    ----------------------------
    Craft a fine-tuned prompt for the observed content in the summary, without including specific content details in the prompt itself and also maintain prompt's original structure,making it more standard, professional and relevant.
    """
  from openai import OpenAI

  completion = OpenAI(api_key = "").chat.completions.create(model = 'gpt-3.5-turbo-16k', temperature = 0,
                                                      messages = [{"role": "system", "content": "You are a prompt engineering expert that is able to generate prompts based on the text that is provided to you."}, {"role": "user", "content": main_prompt}])

  generated_prompt=completion.choices[0].message.content
  with open('prompt.txt', 'w') as file:
          file.write(generated_prompt)
  return prompt_page1_exec+sample_executive_summary+prompt_page2_exec+prompt_page3_exec+generated_prompt+prompt_page4_exec+prompt_page5_exec


@app.route("/intial_exec",methods=["POST","GET"])
def main_page_exec():
  with open('prompt.txt', 'w') as file:
          prompt='''Crafting an engaging executive summary for the Request For Proposal that should incorporates the provided templates and points:
                  At start of the executive summary,
                    Dear [Client's Name],
                    Provide complete overview about the company.
                    Mention about the solution and features offered by the company.
                    Add information about How AI has be incorporated in our solution

                  Middle portion of the executive summary,
                    Start by briefly describing the client's key pain points or challenges to demonstrate your understanding of their needs.
                    Provide a basic overview of the proposed solution.
                    Explain how the company's unique strengths and capabilities effectively address and resolve these challenges.
                    Mention what sets the company apart from the competition to stimulate the client's interest.
                    Conclude the introduction with a positive and emotionally resonant message to leave the client excited about the potential benefits the company can offer.

                    Additionally, the summary should include the following elements:
                      Offer an overview of the document's contents, showcasing key successes, client stories, or standout features that differentiate the company.
                      Summarize the benefits the client will derive from the solution provided by the company, using a clear and concise bullet point format.
                      Highlight the company's key qualifications, with an emphasis on the years of experience and substantial cost savings achieved for previous customers.
                      Mention any extra value-added benefits that the company provides.

                  At the conclusion of the executive summary,
                    Add information about why you are better than any other company in this domain.
                    Highlight the points that why they need us for their problem.
                    The goal is to create an summary that informs, engages, and motivates the client to explore the full Request for Proposal.
                    When crafting the executive summary, assign more importance to avoiding phrases like 'In summary' or 'In conclusion' to enhance its engagement and effectiveness.'''
          file.write(prompt)
  return prompt_page_exec
token_limit_info = {"gpt3.5":4000, "gpt4":8000}

@app.route("/get_relevancy", methods=["POST","GET"])
def result():
    try:

      context = request.form['question_text']


      # read the file, if the content is empty
      if context.strip() == "":
        files = request.files['file']
        context = get_content(files)

      #print(context)
      print("tk",token_len(context))

      if token_len(context) < token_limit_info['gpt4']:
          prompt = '''USER TEXT: All data at rest are encrypted without exception using volume-level encryption using one of the strongest block ciphers available, 256-bit Advanced Encryption Standard (AES-256) in Galois/Counter Mode (GCM), known as AES-GCM.  This includes backups.  All backup volumes are stored encrypted.  Additionally, backups are stored in AWS Regions that are not the primary data centers.  Transmission of this backup data across AWS regions occurs over secure private encrypted channels. \n'''

          prompt += '''GPT RESPONSE: {'Present_Topics': ["Security information", "Data Backups", "Data centers"]} \n\n'''

          prompt += '''USER TEXT: {content}\nGPT RESPONSE: \nBased on the USER TEXT, identify the important TOPICS that are presented'''.format(content=context)


          print("prompt:", prompt)
          openai_result = openai(prompt)
          print("openai_result:-",openai_result)
          print(type(openai_result))
          input_string = openai_result
          start_index = input_string.find("{'Present_Topics': ")
          dict_string = input_string[start_index:]
          end_index = dict_string.find("}")
          dict_string = dict_string[:end_index + 1]
          response_dict = eval(dict_string)
    
          print(openai_result)
          
          output = ''

          for topic in response_dict["Present_Topics"] :
                    output += '<div class="center-container"><span>' + topic + '</span></div><br>'
          prompt = "Identify and return the one common domain based on the below topics. \n"+output
          type_file = openai(prompt)
          print("type",type_file)
          type_file = '<div class="center-container"><span><textarea cols="80" rows="20" style="height:50px;width:1000px;font-size:14pt; background-color:rgb(239, 239, 239);">' + type_file + '</textarea></span></div><br>'+'''
          <form action='topic_analyzer'>
         <button type="submit" class="button">New</button>
      </form>
      <br><br>
      <form action='/'>
         <button type="get_answer" class="button">return to main page</button>
      </form>'''
          
          
      else:
        output = "Token limit Reached"
      result_page = first_page1 + context + first_page2 + output +type_file+ first_page3

      return result_page
    except Exception as e:
      print(e)
      return first_page
      
@app.route("/topic_analyzer",methods=['POST','GET'])
def index_topic():
  with app.app_context():
    return first_page
    
#prompt_context main function
@app.route("/prompt_context",methods=["POST","GET"])
def prompt_context_main():
    return first_page_top10

@app.route("/cosine_score",methods=["POST","GET"])
def cosine_score():
    cosine_score_list=[]
    sentence=request.form.get('sentence').strip()
    list_of_sentence= request.form.get('list_sentence').strip().split("\n")
    emb_model=request.form.get('emb_model')
    emb_sent=get_embedding(sentence,emb_model)
    for i in list_of_sentence:
      emb_list=get_embedding(i.strip(),emb_model)
      cosine_score_list.append([sentence,i.strip(),find_cosine_score([emb_sent],[emb_list])])

    return second_page1_cs + ('\n'.join(map(str, cosine_score_list))) + second_page2_cs + second_page5_cs

#finding cosine score main function
@app.route("/find_cosine_score",methods=["POST","GET"])
def index():
    return first_page_cs

@app.route("/",methods=['POST','GET'])
def main_page():
  return first_page1_main



if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5000, debug=True)

