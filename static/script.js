const rangevalue = document.querySelector(".slider .price-slider");
const rangeInputvalue = document.querySelectorAll(".range-input input");

let priceGap = 500;

const priceInputvalue = document.querySelectorAll(".price-input input");
for (let i = 0; i < priceInputvalue.length; i++) {
    priceInputvalue[i].addEventListener("input", e => {

        let minp = parseInt(priceInputvalue[0].value);
        let maxp = parseInt(priceInputvalue[1].value);
        let diff = maxp - minp

        if (minp < 0) {
            alert("Минимальная цена не может быть меньше 0");
            priceInputvalue[0].value = 0;
            minp = 0;
        }

        if (maxp > 30000) {
            alert("Максимальная цена не может быть больше 30000");
            priceInputvalue[1].value = 30000;
            maxp = 30000;
        }

        if (minp > maxp - priceGap) {
            priceInputvalue[0].value = maxp - priceGap;
            minp = maxp - priceGap;

            if (minp < 0) {
                priceInputvalue[0].value = 0;
                minp = 0;
            }
        }

        if (diff >= priceGap && maxp <= rangeInputvalue[1].max) {
            if (e.target.className === "min-input") {
                rangeInputvalue[0].value = minp;
                let value1 = rangeInputvalue[0].max;
                rangevalue.style.left = `${(minp / value1) * 100}%`;
            }
            else {
                rangeInputvalue[1].value = maxp;
                let value2 = rangeInputvalue[1].max;
                rangevalue.style.right = `${100 - (maxp / value2) * 100}%`;
            }
        }
    });
}

for (let i = 0; i < rangeInputvalue.length; i++) {
    rangeInputvalue[i].addEventListener("input", e => {
        let minVal = parseInt(rangeInputvalue[0].value);
        let maxVal = parseInt(rangeInputvalue[1].value);

        let diff = maxVal - minVal

        if (diff < priceGap) {

            if (e.target.className === "min-range") {
                rangeInputvalue[0].value = maxVal - priceGap;
            }
            else {
                rangeInputvalue[1].value = minVal + priceGap;
            }
        }
        else {

            priceInputvalue[0].value = minVal;
            priceInputvalue[1].value = maxVal;
            rangevalue.style.left = `${(minVal / rangeInputvalue[0].max) * 100}%`;
            rangevalue.style.right = `${100 - (maxVal / rangeInputvalue[1].max) * 100}%`;
        }
    });
}

const quizSteps = document.querySelectorAll(".quiz .step");
const quizButtons = document.querySelectorAll(".quiz_button");

let currentStep = 0;

quizSteps[0].classList.add("active");

for (let i = 0; i < quizButtons.length; i++) {
    quizButtons[i].addEventListener("click", () => {

        if (currentStep < quizSteps.length - 1) {
            quizSteps[currentStep].classList.remove("active");
            currentStep++;
            quizSteps[currentStep].classList.add("active");
        }
    });
}

const quizForm = document.querySelector(".quiz-form");
const quizStatus = document.querySelector(".quiz-status");

function collectQuizChoices(fieldName) {
    const selector = `.quiz input[name="${fieldName}"]:checked`;
    return Array.from(document.querySelectorAll(selector)).map(input => input.value);
}

function setQuizStatus(text, state) {
    if (!quizStatus) {
        return;
    }
    quizStatus.textContent = text;
    quizStatus.className = "quiz-status";
    if (state) {
        quizStatus.classList.add(`quiz-status--${state}`);
    }
}

if (quizForm) {
    const submitButton = quizForm.querySelector(".send-button");

    quizForm.addEventListener("submit", async event => {
        event.preventDefault();

        const payload = {
            user_name: quizForm.user_name.value.trim(),
            user_email: quizForm.user_email.value.trim(),
            types: collectQuizChoices("type"),
            sizes: collectQuizChoices("size")
        };

        if (payload.user_name.length < 2) {
            setQuizStatus("Укажите имя", "error");
            return;
        }

        if (!/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(payload.user_email)) {
            setQuizStatus("Укажите корректный e-mail", "error");
            return;
        }

        submitButton.disabled = true;
        setQuizStatus("Отправляем...", "pending");

        try {
            const response = await fetch(quizForm.action, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok && result.ok) {
                setQuizStatus(result.message, "success");
                quizForm.reset();
            }
            else {
                setQuizStatus(result.message || "Не удалось отправить письмо", "error");
            }
        }
        catch (error) {
            setQuizStatus("Сервер недоступен, попробуйте позже", "error");
        }
        finally {
            submitButton.disabled = false;
        }
    });
}

const instForm = document.querySelector(".inst__form");
const instStatus = document.querySelector(".inst__status");

function setInstStatus(text, state) {
    if (!instStatus) {
        return;
    }
    instStatus.textContent = text;
    instStatus.className = "inst__status";
    if (state) {
        instStatus.classList.add(`inst__status--${state}`);
    }
}

if (instForm) {
    const instButton = instForm.querySelector(".inst__btn");

    instForm.addEventListener("submit", async event => {
        event.preventDefault();

        const payload = {
            user_name: instForm.user_name.value.trim(),
            tel: instForm.tel.value.trim()
        };

        if (payload.user_name.length < 2) {
            setInstStatus("Укажите имя", "error");
            return;
        }

        const digits = payload.tel.replace(/\D/g, "");

        if (digits.length < 10 || digits.length > 15) {
            setInstStatus("Укажите корректный номер телефона", "error");
            return;
        }

        instButton.disabled = true;
        setInstStatus("Отправляем...", "pending");

        try {
            const response = await fetch(instForm.action, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok && result.ok) {
                setInstStatus(result.message, "success");
                instForm.reset();
            }
            else {
                setInstStatus(result.message || "Не удалось отправить заявку", "error");
            }
        }
        catch (error) {
            setInstStatus("Сервер недоступен, попробуйте позже", "error");
        }
        finally {
            instButton.disabled = false;
        }
    });
}
