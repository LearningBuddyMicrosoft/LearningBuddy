import streamlit as st #load streamlit and refer as st
st.set_page_config(layout="wide")
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
if "question_index" not in st.session_state:
    st.session_state.question_index=0

if "submitted" not in st.session_state:
    st.session_state.submitted=False
    
if "answer" not in st.session_state:
    st.session_state.answer = None
if "total" not in st.session_state: 
    st.session_state.total = 0
if "scored" not in st.session_state:
    st.session_state.scored=False
total=0;
questions = [
{"question":"What is the powerhouse of the cell?",
    "options":["A- Mitochondria","B- Chloroplasts","C- Nucleus","D- Ribosomes"],
    "correct_answer":"A- Mitochondria",
    "explanation":"The mitochondria powers the cell",
    "source":"Lecture 1- Cell Biology, slide 3"},
{ "question":"What does DNA stand for?",
    "options":["A- Do Not Ask", "B- Donut Art", "C- Deoxyribonucleic Acid", "D- Dynamic Array"],
    "correct_answer":"C- Deoxyribonucleic Acid",
    "explanation":"Deoxyribonucleic Acid is the full word term",
    "source":"Lecture 3- DNA & RNA, slide 4"},
{"question":"Which of the following are not macronutrients",
    "options":["A- Protein","B- Fats","C- Gluten","D- Carbs"],
    "correct_answer":"C- Gluten",
    "explanation":"Gluten is not a macronutrient",
    "source":"Lecture 5- Nutrition, slide 12"},
{ "question":"What type of blood cell fights infection",
    "options":["A- Red Blood Cell", "B- Blue Blood Cell", "C- Green Blood Cell", "D- White Blood Cell"],
    "correct_answer":"D- White Blood Cell",
    "explanation":"White blood cells fight infection, green and blue dont exist",
    "source":"Lecture 7- Blood, slide 34"},
{"question":"How many pairs of chromosomes in DNA",
    "options":["A- 12","B- 24","C- 48","D- 96"],
    "correct_answer":"B- 24",
    "explanation":"There are 24 pairs",
    "source":"Lecture 6- DNA & RNA, slide 7"}
]
st.title("Learning Buddy")
st.subheader("Question " + str(st.session_state.question_index + 1)+" of "+str(len(questions)))

progress=(st.session_state.question_index+1)/len(questions)
st.progress(progress)
current_question=questions[st.session_state.question_index]

answer = st.radio(current_question["question"], current_question["options"], key=str(st.session_state.question_index))


if st.button("Submit")  and not st.session_state.submitted:#if submit is pressed
    st.session_state.submitted=True
    st.session_state.answer=answer

if st.session_state.submitted:
    if st.session_state.answer == current_question["correct_answer"]:
        st.success("Correct!")
        if not st.session_state.scored:
            st.session_state.total += 1
            st.session_state.scored = True
            st.session_state.scored=True
    else:
        st.error("Incorrect. You selected: "+st.session_state.answer)
        st.write("Correct answer: "+current_question["correct_answer"])
        st.write("Explanation: "+current_question["explanation"])
        st.write("Source: "+current_question["source"])

    if st.session_state.question_index + 1 < len(questions):

        if st.button("Next Question"):
            st.session_state.question_index +=1
            st.session_state.submitted = False
            st.session_state.answer=None
            st.session_state.scored=False
    else:
        st.write("Quiz Complete! You got " +str(st.session_state.total)+"/"+str(len(questions)))
