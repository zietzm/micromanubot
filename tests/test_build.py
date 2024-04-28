import importlib.resources

import micromanubot.build
import micromanubot.template_data.build


def test_parse_templates():
    template_files = importlib.resources.files("micromanubot.template_data.build")
    template_path = template_files.joinpath("main.tex")
    with importlib.resources.as_file(template_path) as file:
        with open(file, "r") as f:
            input_data = f.read()

    templates = micromanubot.build.MainTemplate._parse_templates(input_data)
    correct_templates = [
        "@metadata",
        "@abstract",
        "@main",
        "@supplement",
    ]
    assert templates == correct_templates
