import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "example", ["example2", "example4", "example6", "example_synthetic"]
)
def test_pheno_valid_inputs_run_successfully(
    runner, test_data, tmp_path, example
):
    """Basic smoke test for the "pheno" subcommand"""
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / f"{example}.tsv",
            "--dictionary",
            test_data / f"{example}.json",
            "--output",
            tmp_path,
            "--name",
            "do not care name",
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        tmp_path / "pheno.jsonld"
    ).exists(), "The pheno.jsonld output was not created."


@pytest.mark.parametrize(
    "example,expected_exception,expected_message",
    [
        ("example3", ValueError, ["not a valid Neurobagel data dictionary"]),
        (
            "example_invalid",
            ValueError,
            ["not a valid Neurobagel data dictionary"],
        ),
        ("example7", LookupError, ["not compatible"]),
        ("example8", ValueError, ["more than one column"]),
        (
            "example9",
            LookupError,
            [
                "values not annotated in the data dictionary",
                "'group': ['UNANNOTATED']",
            ],
        ),
        (
            "example11",
            LookupError,
            ["missing values in participant or session id"],
        ),
    ],
)
def test_invalid_inputs_are_handled_gracefully(
    runner, test_data, tmp_path, example, expected_exception, expected_message
):
    """Assures that we handle expected user errors in the input files gracefully"""
    with pytest.raises(expected_exception) as e:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--dataset-dir",
                test_data,
                "--pheno",
                test_data / f"{example}.tsv",
                "--dictionary",
                test_data / f"{example}.json",
                "--output",
                tmp_path,
                "--name",
                "do not care name",
            ],
            catch_exceptions=False,
        )

    for substring in expected_message:
        assert substring in str(e.value)


@pytest.mark.parametrize(
    "option, filepath, expected_exception, expected_message",
    [
        (
            "--pheno",
            "sub_data/example2.tsv",
            IOError,
            "not a top-level file",
        ),
        (
            "--pheno",
            "example2.tsv",
            FileNotFoundError,
            "participants.json not found",
        ),
        (
            "--dictionary",
            "example2.json",
            FileNotFoundError,
            "participants.tsv not found",
        ),
    ],
)
def test_invalid_input_filepaths_handled_gracefully(
    runner,
    test_data,
    tmp_path,
    option,
    filepath,
    expected_exception,
    expected_message,
):
    """Tests that invalid paths for the tabular file and data dictionary result in informative errors."""
    all_args = [
        "pheno",
        "--dataset-dir",
        test_data,
        "--output",
        tmp_path,
        "--name",
        "test dataset 2",
    ] + [option, test_data / filepath]

    with pytest.raises(expected_exception) as e:
        runner.invoke(
            bagel,
            all_args,
            catch_exceptions=False,
        )

    for substring in expected_message:
        assert substring in str(e.value)


@pytest.mark.parametrize(
    "portal",
    [
        "openneuro.org/datasets/ds002080",
        "https://openneuro",
        "not a url",
        "www.github.com/mycoolrepo/mycooldataset",
    ],
)
def test_invalid_portal_uris_raise_error(
    runner,
    test_data,
    tmp_path,
    portal,
):
    """Tests that invalid or non-HTTP/HTTPS URLs result in a user-friendly error."""
    with pytest.raises(ValueError) as e:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--dataset-dir",
                test_data,
                "--pheno",
                test_data / "example2.tsv",
                "--dictionary",
                test_data / "example2.json",
                "--output",
                tmp_path,
                "--name",
                "test dataset 2",
                "--portal",
                portal,
            ],
            catch_exceptions=False,
        )

    assert "not a valid http or https URL" in str(e.value)


def test_unused_missing_values_raises_warning(
    runner,
    test_data,
    tmp_path,
):
    """
    Tests that an informative warning is raised when annotated missing values are not found in the
    phenotypic file.
    """
    with pytest.warns(UserWarning) as w:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--dataset-dir",
                test_data,
                "--pheno",
                test_data / "example10.tsv",
                "--dictionary",
                test_data / "example10.json",
                "--output",
                tmp_path,
                "--name",
                "testing dataset",
            ],
            catch_exceptions=False,
        )

    assert len(w) == 1
    for warn_substring in [
        "missing values in the data dictionary were not found",
        "'group': ['NOT IN TSV']",
        "'tool_item1': ['NOT IN TSV 1', 'NOT IN TSV 2']",
        "'tool_item2': ['NOT IN TSV 1', 'NOT IN TSV 2']",
    ]:
        assert warn_substring in str(w[0].message.args[0])


def test_that_output_file_contains_name(
    runner, test_data, tmp_path, load_test_json
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example2.tsv",
            "--dictionary",
            test_data / "example2.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert pheno.get("hasLabel") == "my_dataset_name"


def test_diagnosis_and_control_status_handled(
    runner, test_data, tmp_path, load_test_json
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example6.tsv",
            "--dictionary",
            test_data / "example6.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert (
        pheno["hasSamples"][0]["hasDiagnosis"][0]["identifier"]
        == "snomed:49049000"
    )
    assert "hasDiagnosis" not in pheno["hasSamples"][1].keys()
    assert "hasDiagnosis" not in pheno["hasSamples"][2].keys()
    assert (
        pheno["hasSamples"][2]["isSubjectGroup"]["identifier"]
        == "purl:NCIT_C94342"
    )


@pytest.mark.parametrize(
    "attribute", ["hasSex", "hasDiagnosis", "hasAssessment", "isSubjectGroup"]
)
def test_controlled_terms_have_identifiers(
    attribute, runner, test_data, tmp_path, load_test_json
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example_synthetic.tsv",
            "--dictionary",
            test_data / "example_synthetic.json",
            "--output",
            tmp_path,
            "--name",
            "do not care name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    for sub in pheno["hasSamples"]:
        if attribute in sub.keys():
            value = sub.get(attribute)
            if not isinstance(value, list):
                value = [value]
            assert all(
                ["identifier" in entry for entry in value]
            ), f"{attribute}: did not have an identifier for subject {sub} and value {value}"


def test_controlled_term_classes_have_uri_type(
    runner, test_data, tmp_path, load_test_json
):
    """Tests that classes specified as schemaKeys (@type) for subject-level attributes in a .jsonld are also defined in the context."""
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example_synthetic.tsv",
            "--dictionary",
            test_data / "example_synthetic.json",
            "--output",
            tmp_path,
            "--name",
            "do not care name",
        ],
    )

    pheno = load_test_json(
        test_data / "example_synthetic.jsonld"
    )  # tmp_path / "pheno.jsonld"

    for sub in pheno["hasSamples"]:
        for key, value in sub.items():
            if not isinstance(value, (list, dict)):
                continue
            if isinstance(value, dict):
                value = [value]
            assert all(
                entry.get("schemaKey", "no schemaKey set") in pheno["@context"]
                for entry in value
            ), f"Attribute {key} for subject {sub} has a schemaKey that does not have a corresponding URI in the context."


@pytest.mark.parametrize(
    "assessment, subject",
    [
        (None, 0),
        (None, 1),
        (
            [
                {"identifier": "cogatlas:1234", "schemaKey": "Assessment"},
                {"identifier": "cogatlas:4321", "schemaKey": "Assessment"},
            ],
            2,
        ),
    ],
)
def test_assessment_data_are_parsed_correctly(
    runner, test_data, tmp_path, load_test_json, assessment, subject
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example6.tsv",
            "--dictionary",
            test_data / "example6.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert assessment == pheno["hasSamples"][subject].get("hasAssessment")


@pytest.mark.parametrize(
    "expected_age, subject",
    [(20.5, 0), (pytest.approx(25.66, 0.01), 1)],
)
def test_cli_age_is_processed(
    runner, test_data, tmp_path, load_test_json, expected_age, subject
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example2.tsv",
            "--dictionary",
            test_data / "example2.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert expected_age == pheno["hasSamples"][subject]["hasAge"]


def test_output_includes_context(runner, test_data, tmp_path, load_test_json):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--dataset-dir",
            test_data,
            "--pheno",
            test_data / "example2.tsv",
            "--dictionary",
            test_data / "example2.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert pheno.get("@context") is not None
    assert all(
        [sub.get("identifier") is not None for sub in pheno["hasSamples"]]
    )
