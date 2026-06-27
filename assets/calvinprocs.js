/*!
* Serialize all form data into an object
* (c) 2021 Chris Ferdinandi, MIT License, https://gomakethings.com
* @param  {FormData} data The FormData object to serialize
* @return {String}        The serialized form data
*/
function serialize(elmnts) {
    let retStr = ''
    // let obj = {};
    for (let theelmnt of elmnts) {
        retStr += theelmnt.name + "='" + theelmnt.value + "';"
    }
    return retStr;
}

//-------------------------------
//-------------------------------
//-------------------------------

//-------------------------------

//-------------------------------


//-------------------------------


var _pj;

var _CONSTANTS, _FUNCTIONS;

function _pj_snippets(container) {
  function in_es6(left, right) {
    if (right instanceof Array || typeof right === "string") {
      return right.indexOf(left) > -1;
    } else {
      if (right instanceof Map || right instanceof Set || right instanceof WeakMap || right instanceof WeakSet) {
        return right.has(left);
      } else {
        return left in right;
      }
    }
  }

  container["in_es6"] = in_es6;
  return container;
}

_pj = {};

_pj_snippets(_pj);

//-------------------------------

/* module for class Parser */

_CONSTANTS = new Map( [
  ["pi", Math.PI],
  ["e", Math.E],
  ["phi", (1 + Math.pow(5, 0.5)) / 2]
]);
_FUNCTIONS = new Map([
    ["abs", Math.abs],
    ["acos", Math.acos],
    ["asin", Math.asin],
    ["atan", Math.atan],
    ["atan2", Math.atan2],
    ["ceil", Math.ceil],
    ["cos", Math.cos],
    ["cosh", Math.cosh],
    ["degrees", Math.degrees],
    ["exp", Math.exp],
    ["fabs", Math.fabs],
    ["floor", Math.floor],
    ["fmod", Math.fmod],
    ["frexp", Math.frexp],
    ["hypot", Math.hypot],
    ["ldexp", Math.ldexp],
    ["log", Math.log],
    ["log10", Math.log10],
    ["modf", Math.modf],
    ["pow", Math.pow],
    ["radians", Math.radians],
    ["sin", Math.sin],
    ["sinh", Math.sinh],
    ["sqrt", Math.sqrt],
    ["tan", Math.tan],
    ["tanh", Math.tanh],
])

class MathParser {
  /*
  class MathParser
  */
  constructor(string, in_vars) {
    this.string = string;
    this.index = 0;
    this.in_vars = in_vars === undefined ? {} : $.extend({}, in_vars);
    
    var constant;
    
    for (var constName in _CONSTANTS) {

      if (constName in this.in_vars) {
        throw "Cannot redefine the value of " + constName;
      }
    }
  }

  getValue() {
    var value;
    value = this.parseExpression();
    this.skipWhitespace();

    if (this.hasNext()) {
      throw "Unexpected character found: '" + this.peek() + "' at index " + this.index.toString();
    }

    return value;
  }

  peek() {
    return this.string.slice(this.index, this.index + 1);
  }

  hasNext() {
    return this.index < this.string.length;
  }

  isNext(value) {
    return this.string.slice(this.index, this.index + value.length) === value;
  }

  popIfNext(value) {
    if (this.isNext(value)) {
      this.index += value.length;
      return true;
    }

    return false;
  }

  popExpected(value) {
    if (!this.popIfNext(value)) {
      throw "Expected '" + value + "' at index " + this.index.toString();
    }
  }

  skipWhitespace() {
    while (this.hasNext()) {
      if (_pj.in_es6(this.peek(), " \t\n\r")) {
        this.index += 1;
      } else {
        return;
      }
    }
  }

  parseExpression() {
    return this.parseAddition();
  }

  parseAddition() {
    var charcter, values, value;
    // values = [this.parseMultiplication()];
    values = [];  values.push(this.parseMultiplication())

    while (true) {
      this.skipWhitespace();
      charcter = this.peek();

      if (charcter === "+") {
        this.index += 1;
        //values.append(this.parseMultiplication());
        values.push(this.parseMultiplication())
      } else {
        if (charcter === "-") {
          this.index += 1;
          //values.append(-1 * this.parseMultiplication());
          values.push(-1 * this.parseMultiplication())
        } else {
          break;
        }
      }
    }

    value = 0.0;
    for (var termindex in values) {
      value += values[termindex];
    }

    return value;
  }

  parseMultiplication() {
    var charcter, denominator, div_index, value, values;
    values = []; values.push(this.parseParenthesis());

    while (true) {
      this.skipWhitespace();
      charcter = this.peek();

      if (charcter === "*") {
        this.index += 1;
        values.push(this.parseParenthesis());
      } else {
        if (charcter === "/") {
          div_index = this.index;
          this.index += 1;
          denominator = this.parseParenthesis();

          if (denominator === 0) {
            throw "Division by 0 kills baby whales (occured at index " + div_index.toString() + ")";
          }

          //values.append(1.0 / denominator);
          values.push(1.0 / denominator);
        } else {
          break;
        }
      }
    }

    value = 1.0;

    //for (var factor, _pj_c = 0, _pj_a = values, _pj_b = _pj_a.length; _pj_c < _pj_b; _pj_c += 1) {
    for (var factorindex in values) {
      value *= values[factorindex];
    }

    return value;
  }

  parseParenthesis() {
    var charcter, value;
    this.skipWhitespace();
    charcter = this.peek();

    if (charcter === "(") {
      this.index += 1;
      value = this.parseExpression();
      this.skipWhitespace();

      if (this.peek() !== ")") {
        throw "No closing parenthesis found at character " + this.index.toString();
      }

      this.index += 1;
      return value;
    } else {
      return this.parseNegative();
    }
  }

  parseArguments() {
    var args;
    args = [];
    this.skipWhitespace();
    this.popExpected("(");

    while (!this.popIfNext(")")) {
      this.skipWhitespace();

      if (args.length > 0) {
        this.popExpected(",");
        this.skipWhitespace();
      }

      args.push(this.parseExpression());
      this.skipWhitespace();
    }

    return args;
  }

  parseNegative() {
    var charcter;
    this.skipWhitespace();
    charcter = this.peek();

    if (charcter === "-") {
      this.index += 1;
      return -1 * this.parseParenthesis();
    } else {
      return this.parseValue();
    }
  }

  parseValue() {
    var charcter;
    this.skipWhitespace();
    charcter = this.peek();

    if (_pj.in_es6(charcter, "0123456789.")) {
      return this.parseNumber();
    } else {
      return this.parseVariable();
    }
  }

  parseVariable() {
    var args, charcter, constant, func, value, vv;
    this.skipWhitespace();
    vv = [];

    while (this.hasNext()) {
      charcter = this.peek();

      if (_pj.in_es6(charcter.toLowerCase(), "_abcdefghijklmnopqrstuvwxyz0123456789")) {
        vv.push(charcter);
        this.index += 1;
      } else {
        break;
      }
    }

    vv = vv.join('');
    func = _FUNCTIONS.get(vv.toLowerCase());

    if (func !== null) {
      args = this.parseArguments();
      return Number.parseFloat(func(...args));
    }

    constant = _CONSTANTS.get(vv.toLowerCase());

    if (constant !== null) {
      return constant;
    }

    value = this.in_vars.get(vv, null);

    if (value !== null) {
      return Number.parseFloat(value);
    }

    throw "Unrecognized variable: '" + vv + "'";
  }

  parseNumber() {
    var charcter, decimal_found, strValue;
    this.skipWhitespace();
    strValue = "";
    decimal_found = false;
    charcter = "";

    while (this.hasNext()) {
      charcter = this.peek();

      if (charcter === ".") {
        if (decimal_found) {
          throw "Found an extra period in a number at character " + this.index.toString() + ". Are you European?";
        }

        decimal_found = true;
        strValue += ".";
      } else {
        if (_pj.in_es6(charcter, "0123456789")) {
          strValue += charcter;
        } else {
          break;
        }
      }

      this.index += 1;
    }

    if (strValue.length === 0) {
      if (charcter === "") {
        throw "Unexpected end found";
      } else {
        throw "I was expecting to find a number at character " + this.index.toString() + " but instead I found a '" + charcter + "'. What's up with that?";
      }
    }

    return Number.parseFloat(strValue);
  }

}

//----------------------

    function math_evaluate(expression, in_vars) {
            pars = new MathParser(expression, in_vars);
        try {
            value = pars.getValue();
        } catch (errr) {
            console.log(errr)
            value = NaN
        }

        if (isNaN(value)) {
            return value
        }
        // Return an integer type if the answer is an integer
        if (Number.isInteger(value)) {
            return parseInt(value)
        }
        // If Javascript made some silly precision error like x.99999999999996, just return x+1 as an integer
        epsilon = 0.0000000001
        if (parseInt(value + epsilon) != parseInt(value)) {
            return parseInt(value + epsilon)
        }
        if (parseInt(value - epsilon) != parseInt(value)) {
            return parseInt(value)
        }
        return value
    }

	// this fn stays.  Too many calls to it.    
    function EvalExpr(expr) {
        try {
            ev = math_evaluate(expr);
        } catch (errr) {
            console.log(errr)
            ev = "????";
        }
        return ev;
    }


// let there be voice!!
const synth = window.speechSynthesis;
const pitch = 1, rate = 1.3;

function speak(textToSpeak) {
    if (textToSpeak !== "") {
        const utterThis = new SpeechSynthesisUtterance(textToSpeak);

        utterThis.onerror = function (event) {
            console.error("SpeechSynthesisUtterance.onerror");
        };

        /* work in preferred voice later ...
        const selectedOption =
            voiceSelect.selectedOptions[0].getAttribute("data-name");

        for (let i = 0; i < voices.length; i++) {
            if (voices[i].name === selectedOption) {
                utterThis.voice = voices[i];
                break;
            }
        }
        */
        utterThis.pitch = pitch;
        utterThis.rate = rate;
        synth.speak(utterThis);
    }
}

