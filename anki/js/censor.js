document.body.innerHTML = document.body.innerHTML.replace(RegExp({{Word}}, "gi"), function (x) { return "_".repeat(x.length) }
