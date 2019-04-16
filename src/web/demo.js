CONSTANTS = ["PI", "E", "TRUE", "FALSE"]
FUNCTIONS = {
    "+": [2], "-": [1, 2], "*": [2], "/": [2], "fabs": [1],
    "<": [2], ">": [2], "==": [2], "!=": [2], "<=": [2], ">=": [2],
    "and": [2], "or": [2],
    "sqrt": [1], "exp": [1], "log": [1], "pow": [2],
    "sin": [1], "cos": [1], "tan": [1], "cot": [1],
    "asin": [1], "acos": [1], "atan": [1],
    "sinh": [1], "cosh": [1], "tanh": [1],
    "asinh": [1], "acosh": [1], "atanh": [1],
    "cbrt": [1], "ceil": [1], "copysign": [2],
    "erf": [1], "erfc": [1], "exp2": [1], "expm1": [1],
    "fdim": [2], "floor": [1], "fma": [3], "fmax": [2],
    "fmin": [2], "fmod": [2], "hypot": [2],
    "j0": [1], "j1": [1], "lgamma": [1], "log10": [1],
    "log1p": [1], "log2": [1], "logb": [1],
    "remainder": [2], "rint": [1], "round": [1],
    "tgamma": [1], "trunc": [1], "y0": [1], "y1": [1]
}

SECRETFUNCTIONS = {"^": "pow", "**": "pow", "abs": "fabs", "min": "fmin", "max": "fmax", "mod": "fmod"}

function tree_errors(tree) /* tree -> list */ {
    var messages = [];
    var names = [];

    bottom_up(tree, function(node, path, parent) {
        switch(node.type) {
        case "ConstantNode":
            if (node.valueType !== "number")
                messages.push("Constants that are " + node.valueType + "s not supported.");
            break;
        case "FunctionNode":
            node.name = SECRETFUNCTIONS[node.name] || node.name;
            if (!FUNCTIONS[node.name]) {
                messages.push("Function <code>" + node.name + "</code> unsupported.");
            } else if (FUNCTIONS[node.name].indexOf(node.args.length) === -1) {
                messages.push("Function <code>" + node.name + "</code> expects " +
                              FUNCTIONS[node.name].join(" or ") + " arguments");
            }
            break;
        case "OperatorNode":
            node.op = SECRETFUNCTIONS[node.op] || node.op;
            if (!FUNCTIONS[node.op]) {
                messages.push("Operator <code>" + node.op + "</code> unsupported.");
            } else if (FUNCTIONS[node.op].indexOf(node.args.length) === -1) {
                messages.push("Operator <code>" + node.op + "</code> expects " +
                              FUNCTIONS[node.op].join(" or ") + " arguments");
            }
            break;
        case "SymbolNode":
            if (CONSTANTS.indexOf(node.name) === -1)
                names.push(node.name);
            break;
        default:
            messages.push("Unsupported syntax; found unexpected <code>" + node.type + "</code>.")
            break;
        }
    });

    return messages;
}

function bottom_up(tree, cb) {
    if (tree.args) {
        tree.args = tree.args.map(function(node) {return bottom_up(node, cb)});
        tree.res = cb(tree);
    } else {
        tree.res = cb(tree);
    }
    return tree;
}

function dump_fpcore(formula, pre, precision) {
    var tree = math.parse(formula);
    var ptree = math.parse(pre);

    var names = [];
    var body = dump_tree(tree, names);
    var precondition = dump_tree(ptree, names);

    var dnames = [];
    for (var i = 0; i < names.length; i++) {
        if (dnames.indexOf(names[i]) === -1) dnames.push(names[i]);
    }

    var name = formula.replace("\\", "\\\\").replace("\"", "\\\"");
    var fpcore = "(FPCore (" + dnames.join(" ") + ") :name \"" + name + "\"";
    if (pre) fpcore += " :pre " + precondition;
    if (precision) fpcore += " :precision " + precision;

    return fpcore + " "  + body + ")";
}

function is_comparison(name) {
    return ["==", "!=", "<", ">", "<=", ">="].indexOf(name) !== -1;
}

function flatten_comparisons(node) {
    var terms = [];
    (function collect_terms(node) {
        if (node.type == "OperatorNode" && is_comparison(node.name)) {
            collect_terms(node.args[0]);
            collect_terms(node.args[1]);
        } else {
            terms.push(node.res);
        }
    })(node);
    var conjuncts = [];
    (function do_flatten(node) {
        if (node.type == "OperatorNode" && is_comparison(node.name)) {
            do_flatten(node.args[0]);
            var i = conjuncts.length;
            conjuncts.append("(" + node.op + " " + terms[i] + " " + terms[i+1] + ")");
            do_flatten(node.args[1]);
        }
    })(node);
    return "(and " + conjuncts.join(" ") + ")";
}

function dump_tree(tree, names) {
    function extract(args) {return args.map(function(n) {return n.res});}
    return bottom_up(tree, function(node) {
        switch(node.type) {
        case "ConstantNode":
            return "" + node.value;
        case "FunctionNode":
            node.name = SECRETFUNCTIONS[node.name] || node.name;
            return "(" + node.name + " " + extract(node.args).join(" ") + ")";
        case "OperatorNode":
            node.op = SECRETFUNCTIONS[node.op] || node.op;
            if (is_comparison(node.name)) {
                return flatten_comparison(node);
            } else {
                return "(" + node.op + " " + extract(node.args).join(" ") + ")";
            }
        case "SymbolNode":
            if (CONSTANTS.indexOf(node.name) === -1)
                names.push(node.name);
            return node.name;
        case "ConditionalNode":
            return "(if " + extract(node.condition) + 
                " " + extract(node.trueExpr) + 
                " " + extract(node.falseExpr) + ")";
        default:
            throw SyntaxError("Invalid tree!");
        }
    }).res;
}

function get_errors() {
    var tree, errors = [];
    for (var i = 0; i < arguments.length; i++) {
        try {
            tree = math.parse(arguments[i]);
            errors = errors.concat(tree_errors(tree));
        } catch (e) {
            errors.push("" + e);
        }
    }
    return errors;
}

function check_errors() {
    var input = document.querySelector("#formula input[name=formula-math]");
    var pre = document.querySelector("#formula input[name=pre-math]");
    var errors = get_errors(input.value, pre.value || "TRUE");

    if (input.value && errors.length > 0) {
        document.getElementById("errors").innerHTML = "<li>" + errors.join("</li><li>") + "</li>";
    } else {
        document.getElementById("errors").innerHTML = "";
    }
}

function hide_extra_fields() {
    var $extra = document.querySelector("#formula .extra-fields");
    var inputs = $extra.querySelectorAll("input, select");
    for (var i = 0; i < inputs.length; i++) {
        if (inputs[i].tagName == "INPUT" && inputs[i].value) return;
        if (inputs[i].tagName == "SELECT" && inputs[i].selectedIndex) return;
    }
    var $a = document.createElement("a");
    $a.textContent = "Additional options »";
    $a.classList.add("show-extra");
    $extra.parentNode.insertBefore($a, $extra.nextSibling);
    $extra.style.display = "none";
    $a.addEventListener("click", function() {
        $extra.style.display = "block";
        $a.style.display = "none";
    });
}

function onload() {
    var form = document.getElementById("formula");
    var input = document.querySelector("#formula input[name=formula]");
    input.setAttribute("name", "formula-math");
    input.setAttribute("placeholder", "sqrt(x + 1) - sqrt(x)");
    input.removeAttribute("disabled");
    var pre = document.querySelector("#formula input[name=pre]");
    pre.setAttribute("name", "pre-math");
    pre.setAttribute("placeholder", "TRUE");
    pre.removeAttribute("disabled");
    var prec = document.querySelector("#formula select[name=precision]");
    var hinput = document.createElement("input");
    hinput.type = "hidden";
    hinput.setAttribute("name", "formula");
    form.appendChild(hinput);
    hide_extra_fields();

    document.getElementById("mathjs-instructions").style.display = "block";
    document.getElementById("lisp-instructions").style.display = "none";

    input.addEventListener("keyup", check_errors);
    pre.addEventListener("keyup", check_errors);

    form.addEventListener("submit", function(evt) {
        var errors = get_errors(input.value, pre.value || "TRUE");
        if (errors.length > 0) {
            document.getElementById("errors").innerHTML = "<li>" + errors.join("</li><li>") + "</li>";
            evt.preventDefault();
            return false;
        } else {
            document.getElementById("errors").innerHTML = "";
        }

        var fpcore = dump_fpcore(input.value, pre.value, prec.value);
        hinput.setAttribute("value", fpcore);

        var url = document.getElementById("formula").getAttribute("data-progress");
        if (url) {
            input.disabled = "true";
            ajax_submit(url, fpcore);
            evt.preventDefault();
            return false;
        } else {
            return true;
        }
    });
}

function clean_progress(str) {
    var lines = str.split("\n");
    var outlines = [];
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        var words = line.split("  ");
        var word0 = words.shift();
        outlines.push((word0.substring(0, 6) === "* * * " ? "* " : "") + words.join("  "));
    }
    return outlines.join("\n");
}

function get_progress(loc) {
    var req2 = new XMLHttpRequest();
    req2.open("GET", loc);
    req2.onreadystatechange = function() {
        if (req2.readyState == 4) {
            if (req2.status == 202) {
                document.getElementById("progress").textContent = clean_progress(req2.responseText);
                setTimeout(function() {get_progress(loc)}, 100);
            } else if (req2.status == 201) {
                var loc2 = req2.getResponseHeader("Location");
                window.location.href = loc2;
            } else {
                document.getElementById("errors").innerHTML = req2.responseText;
            }
        }
    }
    req2.send();
}

function ajax_submit(url, lisp) {
    document.getElementById("progress").style.display = "block";
    var req = new XMLHttpRequest();
    req.open("POST", url);
    req.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    req.onreadystatechange = function() {
        if (req.readyState == 4) {
            if (req.status == 201) {
                var jobcount = req.getResponseHeader("X-Job-Count");
                var jobelt = document.getElementById("num-jobs")
                if (jobelt) jobelt.innerHTML = Math.max(jobcount - 1, 0);
                var loc = req.getResponseHeader("Location");
                get_progress(loc);
            } else {
                document.getElementById("errors").innerHTML = req.responseText;
            }
        }
    }
    var content = "formula=" + encodeURIComponent(lisp);
    req.send(content);
}

window.addEventListener("load", onload);
