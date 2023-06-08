import numpy
import pandas
from pandas import Series
from matplotlib import pyplot
import seaborn


def ageF(data_frame: pandas.DataFrame) -> pandas.DataFrame:
    age_field = "Age"

    return data_frame.mask((data_frame[age_field] > 100) | (data_frame[age_field] < 15))


def genderF(data_frame: pandas.DataFrame) -> pandas.DataFrame:
    gender_field = "Gender"

    female_prefix = "f"
    male_prefix = "m"

    data_frame.loc[
        ~(
            data_frame[gender_field]
            .str.lower()
            .str.startswith((female_prefix, male_prefix), na=False)
        ),
        gender_field,
    ] = 2
    data_frame.loc[
        data_frame[gender_field].str.lower().str.startswith(male_prefix, na=False),
        gender_field,
    ] = 0
    data_frame.loc[
        data_frame[gender_field].str.lower().str.startswith(female_prefix, na=False),
        gender_field,
    ] = 1
    return data_frame


def uniqueValuesF(data_frame: pandas.DataFrame) -> pandas.DataFrame:
    fields = ("leave", "no_employees", "work_interfere")
    for field in fields:
        uniq_values = data_frame[field].unique()
        for i, uniq_value in enumerate(uniq_values):
            data_frame.loc[data_frame[field] == uniq_value, field] = i

    return data_frame


def binaryFieldsF(data_frame: pandas.DataFrame) -> pandas.DataFrame:
    yes_value = "Yes"
    no_value = "No"

    binary_fields = (
        "family_history",
        "treatment",
        "remote_work",
        "tech_company",
        "benefits",
        "care_options",
        "wellness_program",
        "seek_help",
        "anonymity",
        "mental_health_consequence",
        "phys_health_consequence",
        "coworkers",
        "supervisor",
        "mental_health_interview",
        "phys_health_interview",
        "mental_vs_physical",
        "obs_consequence",
        "self_employed",
    )
    for field in binary_fields:
        data_frame.loc[
            (data_frame[field] != no_value) & (data_frame[field] != yes_value), field
        ] = None
        data_frame.loc[data_frame[field] == no_value, field] = 0
        data_frame.loc[data_frame[field] == yes_value, field] = 1

    return data_frame


def dataF(filename: str, result_filename: str):
    data_frame = pandas.read_csv(filename)

    data_frame = ageF(data_frame)
    data_frame = genderF(data_frame)
    data_frame = uniqueValuesF(data_frame)
    data_frame = binaryFieldsF(data_frame)

    data_frame.to_csv(result_filename)


def analyze_data(filename: str) -> list[str]:
    data_frame = pandas.read_csv(filename)

    math_expected_values = pandas.DataFrame()
    expectation_dataframe = pandas.DataFrame()

    for column in data_frame.columns.values[2:-1]:
        expectation_dataframe = pandas.concat(
            [
                expectation_dataframe,
                pandas.DataFrame(
                    data_frame.groupby(column).size() / len(data_frame),
                    columns=[column],
                ),
            ]
        )
        res: Series = (
            data_frame[column].value_counts() / data_frame[column].count()
        ) * 100
        text = f"{res.name}:\n{res.to_string(min_rows=2, max_rows=2)}\n"

        if column not in ("Country", "state"):
            text += f"Дисперсия - {data_frame[column].var()}\nСреднее - {data_frame[column].mean()}\n"
            math_expected_values[column] = pandas.Series(data_frame[column].mean())

        print(text)


    important_fields = []
    for column in data_frame.columns.values[2:-1]:
        if column in ("Country", "state"):
            continue

        important_field = str(
            numpy.where(
                expectation_dataframe[column].idxmax()
                > math_expected_values[column].max(),
                column,
                numpy.NaN,
            )
        )
        if important_field != "nan":
            important_fields.append(important_field)

    print(f"Потенциальные ключевые признаки псих. заболеваний - {important_fields}")
    return important_fields


def vis_data(filename: str, important_fields: list[str]):
    data_frame = pandas.read_csv(filename)
    pyplot.figure(figsize=(12, 15))

    diagram_data_frame = pandas.DataFrame(
        {
            field: pandas.Series(data_frame.groupby(field).size() / len(data_frame))
            for field in important_fields
        }
    )
    print(diagram_data_frame)

    seaborn.heatmap(diagram_data_frame, cmap="Spectral", annot=True)
    pyplot.xticks(rotation=90)
    pyplot.title(
        "Визуализация долей каждого варианта значимых столбцов",
        color="#29452b",
        weight="semibold",
        fontsize=16,
        alpha=0.6,
    )
    pyplot.savefig("important_fields_parts.png")
    pyplot.clf()

    correlation = data_frame.corr(numeric_only=True)
    mask = numpy.zeros_like(correlation, dtype=bool)
    mask[numpy.triu_indices_from(mask)] = True
    seaborn.heatmap(
        correlation,
        mask=mask,
        cmap="viridis",
        vmax=0.3,
        center=0,
        square=True,
        cbar_kws={"shrink": 0.5},
        annot=True,
        fmt=".3f",
        annot_kws={"size": 6},
    )
    pyplot.savefig("correlation.png")
    pyplot.clf()
    pyplot.subplots(figsize=(7, 7))

    pyplot.grid()
    for column in diagram_data_frame.columns.tolist():
        pyplot.grid()
        field_data_frame = pandas.DataFrame(
            {column: pandas.Series(data_frame.groupby(column).size())}
        )
        plots = seaborn.barplot(
            x=list(field_data_frame.index),
            y=field_data_frame[column],
            data=field_data_frame,
            width=0.43,
            palette="mako",
        )
        pyplot.xlabel("Variable", size=15)
        pyplot.ylabel("Iteration", size=15)
        for bar in plots.patches:
            pyplot.annotate(
                format(int(bar.get_height()), ".2f"),
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center",
                va="center",
                size=10,
                xytext=(0, 5),
                textcoords="offset points",
            )
        plots.set_title(f"Количество и вариация элементов в столбцe {column}")
        pyplot.savefig(f"{column}.png")


def get_stat(filename: str):
    data_frame = pandas.read_csv(filename)

    treatment_probability = data_frame.groupby("treatment").size() / len(data_frame)
    treatment_no_probability = treatment_probability.iloc[0]
    treatment_yes_probability = treatment_probability.iloc[1]
    treatment_confirm_probability = (
        treatment_yes_probability
        * (
            treatment_yes_probability
            + treatment_no_probability
            / treatment_yes_probability
            * treatment_no_probability
        )
    ) / (treatment_no_probability + treatment_yes_probability)

    print(
        f"Вероятность обращения за лечением - {round(treatment_confirm_probability, 2)}%"
    )

    treatment_probability = data_frame.groupby("treatment").size()
    treatment_no_probability = treatment_probability.iloc[0]
    treatment_yes_probability = treatment_probability.iloc[1]
    treatment_cancel_probability = (
        treatment_no_probability
        + (
            (treatment_yes_probability + treatment_no_probability)
            / (treatment_yes_probability * treatment_no_probability)
        )
    ) / (len(data_frame))

    print(
        f"Вероятность НЕ обращения за лечением - {round(treatment_cancel_probability, 2)}%"
    )

    work_interference_probability = data_frame.groupby("work_interfere").size() / len(
        data_frame
    )
    work_interference_probability_often = work_interference_probability.iloc[0]
    work_interference_probability_rarely = work_interference_probability.iloc[1]
    work_interference_probability_never = work_interference_probability.iloc[2]
    work_interference_probability_sometimes = work_interference_probability.iloc[3]

    work_interference_probability_often_result = (
        (
            work_interference_probability_rarely
            + work_interference_probability_never
            + work_interference_probability_sometimes
        )
        * (
            (
                (
                    work_interference_probability_rarely
                    * work_interference_probability_never
                    * work_interference_probability_sometimes
                    * work_interference_probability_often
                )
                * (
                    work_interference_probability_rarely
                    + work_interference_probability_never
                    + work_interference_probability_sometimes
                )
            )
            / work_interference_probability_often
        )
    ) / (work_interference_probability_often)
    work_interference_probability_rare_result = (
        (
            work_interference_probability_often
            + work_interference_probability_never
            + work_interference_probability_sometimes
        )
        * (
            (
                (
                    work_interference_probability_often
                    * work_interference_probability_never
                    * work_interference_probability_sometimes
                    * work_interference_probability_rarely
                )
                * (
                    work_interference_probability_often
                    + work_interference_probability_never
                    + work_interference_probability_sometimes
                )
            )
            / work_interference_probability_rarely
        )
    ) / (work_interference_probability_rarely)
    work_interference_probability_never_result = (
        (
            work_interference_probability_rarely
            + work_interference_probability_often
            + work_interference_probability_sometimes
        )
        * (
            (
                (
                    work_interference_probability_rarely
                    * work_interference_probability_never
                    * work_interference_probability_sometimes
                    * work_interference_probability_often
                )
                * (
                    work_interference_probability_rarely
                    + work_interference_probability_never
                    + work_interference_probability_sometimes
                )
            )
            / work_interference_probability_never
        )
    ) / (
        work_interference_probability_never
    )
    work_interference_probability_sometimes_result = (
        (
            work_interference_probability_rarely
            + work_interference_probability_never
            + work_interference_probability_often
        )
        * (
            (
                (
                    work_interference_probability_rarely
                    * work_interference_probability_never
                    * work_interference_probability_sometimes
                    * work_interference_probability_often
                )
                * (
                    work_interference_probability_rarely
                    + work_interference_probability_never
                    + work_interference_probability_often
                )
            )
            / work_interference_probability_sometimes
        )
    ) / (
        work_interference_probability_sometimes
    )

    print(
        f"психические проблемы часто мешают в работе - {round(work_interference_probability_often_result,2)}%"
    )
    print(
        f"психические проблемы редко мешают в работе - {round(work_interference_probability_rare_result, 2)}%"
    )
    print(
        f"психические проблемы никогда мешают в работе - {round(work_interference_probability_never_result, 4)}%"
    )
    print(
        f"психические проблемы иногда мешают в работе - {round(work_interference_probability_sometimes_result, 4)}%"
    )

    coworkers_probability = data_frame.groupby("coworkers").size() / len(data_frame)
    coworkers_probability_no = coworkers_probability.iloc[0]
    coworkers_probability_yes = coworkers_probability.iloc[1]

    coworkers_probability_result = (
        coworkers_probability_yes
        * (
            (coworkers_probability_yes + coworkers_probability_no)
            / coworkers_probability_yes
            * coworkers_probability_no
        )
    ) / (coworkers_probability_no + coworkers_probability_yes)
    print(
        f"Вероятность обсудидения своего психического здоровья с коллегами - {round(coworkers_probability_result, 4)}%"
    )


def sickF(filename: str, human_index: int, important_fields: list[str]):
    human_frame = pandas.read_csv(filename).iloc[human_index]

    value = sum([human_frame[field] for field in important_fields if not numpy.isnan(human_frame[field])])
    schizophrenia_probability = value / len(important_fields)
    print(f"Человек №{human_index} болен с вероятностью {round(schizophrenia_probability, 5)}%")


if __name__ == "__main__":
    data_filename = "result.csv"
    dataF("survey.csv", data_filename)
    _important_fields = analyze_data(data_filename)
    vis_data(data_filename, _important_fields)
    get_stat(data_filename)
    sickF(data_filename, 123, _important_fields)