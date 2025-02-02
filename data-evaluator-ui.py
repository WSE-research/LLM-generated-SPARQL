import json
import streamlit as st
import os
import math
import matplotlib.pyplot as plt

PROCESSES = ["direct", "NER", "masked"]


def read_data(file):
    with open(f"data/{file}", "r") as f:
        data = f.readlines()
    return data


ICON_NOT_VALID = "🚫"
ICON_ERROR = "❌"
ICON_CORRECT = "✅"
ICON_INCORRECT = "⚠️"
ICON_UNKNOWN = "❓"
ICON_SPARQL_QUERY_INCORRECT = "🛑"


def get_prepared_results(data):
    global ICON_NOT_VALID
    global ICON_ERROR
    global ICON_CORRECT
    global ICON_INCORRECT
    global ICON_UNKNOWN

    valid_query = data.get("valid_query")
    error = data.get("error")
    correct = data.get("correct")

    if valid_query != True:
        icon = ICON_NOT_VALID
        message = "Invalid response(the query was NOT successfully extracted from LLM response or has NOT passed RDFlib syntax check 'error' contains reason to fail). Error: {error}"
    elif error != None:
        icon = ICON_ERROR
        message = "Error response: should not be here if valid_query is None"
    elif correct == True:
        icon = ICON_CORRECT
        message = "Correct response: query returns non-empty list, and set of returned URIs is equal to set of URIs from the gold standard"
    else:
        icon = ICON_INCORRECT
        message = "Incorrect response: query returns empty list, or set of returned URIs is not equal to set of URIs from the gold standard"

    return icon, message


def get_item(data):
    question = data.get("question")
    model = data.get("model")
    process = data.get("process")
    prompt = data.get("prompt")
    response = data.get("response")
    normal_query = data.get("normal_query")
    valid_query = data.get("valid_query")
    error = data.get("error")
    correct = data.get("correct")
    # define icon based on error, valid_query, correct
    icon, message = get_prepared_results(data)
    return question, model, process, prompt, response, normal_query, valid_query, error, correct, icon, message


def check_sparql_query(normal_query):
    if normal_query != None and ("SELECT" in normal_query or "ASK" in normal_query):
        return True
    return False


def main():
    global PROCESSES
    global ICON_NOT_VALID
    global ICON_ERROR
    global ICON_CORRECT
    global ICON_INCORRECT
    global ICON_UNKNOWN

    icons = [ICON_CORRECT, ICON_INCORRECT, ICON_NOT_VALID]

    # use wide mode for better layout
    st.set_page_config(layout="wide")

    st.title("Data Evaluator UI")

    st.sidebar.header("Choose data source")

    # read all files from folder data
    files = os.listdir("data")

    # select from existing files in folder data
    st.sidebar.subheader("Select from existing files")
    file = st.sidebar.selectbox("Select file", files)

    # read JSONL data from selected file
    data = read_data(file)

    # collect all model names from the data
    tabulated_data_rows_ids = {}
    for line in data:
        line = json.loads(line)
        model = line.get("model")
        if model not in tabulated_data_rows_ids:
            tabulated_data_rows_ids[model] = []
        tabulated_data_rows_ids[model].append(line)
    # remove duplicates
    tabulated_data_rows_ids = list(tabulated_data_rows_ids.keys())
    tabulated_data_rows_ids.sort()

    # collect all process names from the data
    tabulated_data_column_ids = {}
    for line in data:
        line = json.loads(line)
        process = line.get("process")
        if process not in tabulated_data_column_ids:
            tabulated_data_column_ids[process] = []
        tabulated_data_column_ids[process].append(line)
    # remove duplicates
    tabulated_data_column_ids = list(tabulated_data_column_ids.keys())

    # warn if process names are not the same
    if tabulated_data_column_ids != PROCESSES:
        st.warning(
            f"Process names in the data are different from the expected ones: {tabulated_data_column_ids} (expected: {PROCESSES})")

    # create a dictionary to store statistics
    statistics = {}
    statistics_extra = {}

    for model in tabulated_data_rows_ids:
        statistics[model] = {}
        statistics_extra[model] = {}
        for process in PROCESSES:
            statistics[model][process] = {}
            statistics_extra[model][process] = {}

    number_of_experiments_per_question = len(PROCESSES) * len(
        tabulated_data_rows_ids)

    # slider to select number of experiments
    # divide lines by number of experiments per question
    max_questions = math.ceil(len(data) / number_of_experiments_per_question)

    number_of_questions = st.sidebar.slider(
        "Show this number of questions", 1, max_questions, 50)

    first_question = st.sidebar.slider(
        "ID of first question to be shown", 0, max_questions - 1, 50)

    # sort data
    data.sort()
    # organize all data
    tabulated_data = {}
    for line in data:
        line = json.loads(line)
        question = line.get("question")
        model = line.get("model")
        process = line.get("process")

        # check and initialize the dictionary
        if question not in tabulated_data:
            tabulated_data[question] = {}
        for process_original in PROCESSES:
            if process_original not in tabulated_data[question]:
                tabulated_data[question][process] = {}
        for model_original in tabulated_data_rows_ids:
            if model_original not in tabulated_data[question][process]:
                tabulated_data[question][process][model_original] = []

        tabulated_data[question][process][model].append(line)
        question, model, process, prompt, response, normal_query, valid_query, error, correct, icon, message = get_item(
            line)
        # increase number of icons in statistics
        if icon not in statistics[model][process]:
            statistics[model][process][icon] = 0
        statistics[model][process][icon] += 1

        if ICON_SPARQL_QUERY_INCORRECT not in statistics_extra[model][process]:
            statistics_extra[model][process][ICON_SPARQL_QUERY_INCORRECT] = 0

        if icon == ICON_NOT_VALID:
            # check if normal_query contains SELECT or ASK
            if normal_query == None:
                pass
            elif not check_sparql_query(normal_query):
                statistics_extra[model][process][ICON_SPARQL_QUERY_INCORRECT] += 1

                # display statistics

                # for each process in a column
    process_columns = st.columns(len(PROCESSES)+1, border=True)
    with process_columns[0]:
        st.subheader("Statistics")

    for j, process in enumerate(PROCESSES):
        with process_columns[j+1]:
            st.subheader(f"{process}")

    # for each process in a column
    for model in tabulated_data_rows_ids:
        process_columns = st.columns(len(PROCESSES)+1, border=True)
        with process_columns[0]:
            st.write(f"{model}")

        for j, process in enumerate(PROCESSES):
            with process_columns[j+1]:
                # icons = statistics[model][process].keys()
                # sort icons
                # icons = sorted(icons)
                count = 0
                for icon in icons:
                    if icon not in statistics[model][process]:
                        statistics[model][process][icon] = 0
                    else:
                        count += statistics[model][process][icon]

                left_statistics, right_statistics = st.columns(2)
                with left_statistics:
                    for icon in icons:
                        st.write(
                            f"{icon} : {statistics[model][process][icon]} → {statistics[model][process][icon]/count:.1%}")
                    st.write(f"= {count}")
                    st.write(
                        f"{ICON_SPARQL_QUERY_INCORRECT} SELECT OR ASK missing: {statistics_extra[model][process][ICON_SPARQL_QUERY_INCORRECT]}")
                with right_statistics:
                    # plot the data
                    fig, ax = plt.subplots()

                    chart_values = statistics[model][process]
                    # sort by keys to have the same order in the chart
                    chart_values = dict(sorted(chart_values.items()))

                    values = chart_values.values()
                    # fix zero values in the dict_values to avoid error in the chart
                    values = [v if v > 0 else 0.000001 for v in values]

                    labels = chart_values.keys()
                    # define colors for each icon in the chart
                    colors = ['gold', 'green', 'red']
                    explode = (0, 0.15, 0)
                    ax.pie(values, labels=labels, autopct='%1.1f%%',
                           colors=colors, textprops={'fontsize': 18}, explode=explode)
                    st.pyplot(fig)

    process_columns = st.columns(len(PROCESSES)+1, border=True)
    with process_columns[0]:
        st.write("total:")

    for j, process in enumerate(PROCESSES):
        with process_columns[j+1]:
            total = 0
            for model in tabulated_data_rows_ids:
                for icon in statistics[model][process]:
                    total += statistics[model][process][icon]
            st.write(f"= {total}")

    # remove all data before the question at position first_question
    for i in range(first_question-1):
        tabulated_data.pop(i, None)

    # data = data[:number_of_experiments_per_question * number_of_experiments]
    tabulated_data = dict(list(tabulated_data.items())[:number_of_questions])

    # display data in table
    for i, question in enumerate(tabulated_data):
        st.subheader(f"Question {i + first_question}: {question}")
        number_of_columns = len(PROCESSES) + 1

        process_columns = st.columns(number_of_columns, border=True)

        with process_columns[0]:
            on_all = st.toggle(
                "show all details of this question", key=question)

        # show the process names
        for j, process in enumerate(PROCESSES):
            with process_columns[j+1]:
                st.write(process)

        # show results for each model
        if process not in tabulated_data[question]:
            st.write(f"No data: {question} {process}")
            with st.expander("Details", icon=ICON_ERROR):
                st.code(json.dumps(tabulated_data[question], indent=2))

        for model in tabulated_data_rows_ids:
            process_columns = st.columns(number_of_columns, border=True)
            with process_columns[0]:
                # show the short process results
                short_results = ""
                # for process in tabulated_data[question]:
                #     icon, message = get_prepared_results(line)
                #     short_results += f"{icon}"
                left_column = st.columns(2)
                left_column[0].write(model)
                with left_column[1]:
                    # a button to show the complete results
                    on = st.toggle("show details", key=question+model)
                # st.write(model + " : " + short_results)

            for j, process in enumerate(PROCESSES):
                with process_columns[j+1]:
                    if process not in tabulated_data[question]:
                        st.write(
                            f"No process data found: {question} {process}")
                        # show the details with error icon
                        with st.expander("Details", icon=ICON_ERROR):
                            st.code(json.dumps(
                                tabulated_data[question], indent=2))
                        continue

                    if model not in tabulated_data[question][process]:
                        st.write(
                            f"No model data found: {question} {process} {model}", icon=ICON_ERROR)
                        with st.expander("Details"):
                            st.code(
                                json.dumps(tabulated_data[question][process], indent=2))
                        continue

                    for line in tabulated_data[question][process][model]:
                        question, model, process, prompt, response, normal_query, valid_query, error, correct, icon, message = get_item(
                            line)

                        if on == False and on_all == False:
                            if icon == ICON_NOT_VALID and not check_sparql_query(normal_query):
                                st.write(icon + ICON_SPARQL_QUERY_INCORRECT)
                            else:
                                st.write(icon)
                            continue

                        st.code(prompt, language="text", wrap_lines=True)

                        with st.expander(f"{icon} Response Details: {message} <br>// error: {error} // valid_query: {valid_query} // correct: {correct}"):
                            st.write(
                                f"Eval: Error: {error}, valid_query: {valid_query}, correct: {correct}")
                            st.code(response, language="json")

                        st.write("Generated Query (`normal_query`):")
                        # quick format of the SPARQL query while adding line breaks
                        normal_query = normal_query.replace("SELECT", "\nSELECT").replace(
                            "WHERE", "\nWHERE").replace("FILTER", "\nFILTER").replace("OPTIONAL", "\nOPTIONAL").replace("UNION", "\nUNION").replace("LIMIT", "\nLIMIT").replace("ORDER BY", "\nORDER BY")
                        if not check_sparql_query(normal_query):
                            st.write(ICON_SPARQL_QUERY_INCORRECT)

                        st.code(normal_query)
                        # collapse accordion to show details
                        with st.expander("Details"):
                            st.code(json.dumps(line, indent=2),
                                    language="json")


if __name__ == "__main__":
    main()
