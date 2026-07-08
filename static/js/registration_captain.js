function updateSubmitButton() {
  const submitButton = document.getElementById('joinTeamButton');
  const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]), select'));
  const allFieldsValid = inputs.every(function (input) {
    return validateField(input);
  });

  submitButton.disabled = !allFieldsValid;
  submitButton.classList.toggle('disabled_button', !allFieldsValid);
}

function isValidName(value) {
  return value !== '' && value.length < 128 && /^[A-Za-z' -]+$/.test(value);
}

function isValidPhone(value) {
  return value.length >= 10 && value.length <= 15 && /^[0-9-]+$/.test(value);
}

function isValidGender(value) {
  return isValidName(value);
}

function validateField(input) {
  const name = input.name;
  const value = input.value.trim();
  let isValid = true;

  switch (name) {
    case 'first_name':
    case 'last_name':
      isValid = isValidName(value);
      break;
    case 'gender':
      isValid = isValidGender(value);
      break;
    case 'phone_number':
      isValid = isValidPhone(value);
      break;
    default:
      isValid = value !== '';
  }

  input.classList.toggle('invalid_input', !isValid);
  return isValid;
}

document.addEventListener('DOMContentLoaded', function () {
  const submitButton = document.getElementById('joinTeamButton');
  const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]), select'));

  submitButton.disabled = true;
  submitButton.classList.add('disabled_button');

  inputs.forEach(function (input) {
    input.addEventListener('input', function () {
      validateField(input);
      updateSubmitButton();
    });
    input.addEventListener('change', function () {
      validateField(input);
      updateSubmitButton();
    });
  });

  updateSubmitButton();
});