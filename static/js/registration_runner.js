function openWaiver() {
  document.getElementById('waiverCheckbox').disabled = false;
  window.open('/static/waiver.pdf', '_blank');
}

function updateSubmitButton() {
  const checkbox = document.getElementById('waiverCheckbox');
  const submitButton = document.getElementById('joinTeamButton');
  const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]), select'));
  const allFieldsValid = inputs.every(function (input) {
    return validateField(input);
  });
  const canSubmit = checkbox.checked && allFieldsValid;

  submitButton.disabled = !canSubmit;
  submitButton.classList.toggle('disabled_button', !canSubmit);
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

function getSelectedTeamDivision() {
  const teamSelect = document.querySelector('select[name="team_id"]');
  if (!teamSelect) {
    return null;
  }

  const selectedOption = teamSelect.options[teamSelect.selectedIndex];
  if (!selectedOption || !selectedOption.textContent) {
    return null;
  }

  const match = selectedOption.textContent.match(/\((open|mixed|master)\)$/i);
  return match ? match[1].toLowerCase() : null;
}

function isValidAge(value) {
  if (!/^\d+$/.test(value)) {
    return false;
  }
  const age = parseInt(value, 10);
  if (age < 1 || age > 100) {
    return false;
  }

  const division = getSelectedTeamDivision();
  if (division === 'master') {
    return age >= 50;
  }
  if (division === 'open' || division === 'mixed') {
    return age >= 15;
  }
  return true;
}

function isValidTeamSelection(value) {
  return value !== '' && value !== 'undefined';
}

function isValidToken(value) {
  return value.trim() !== '';
}

function validateField(input) {
  const name = input.name;
  const value = input.value.trim();
  let isValid = true;

  switch (name) {
    case 'first_name':
    case 'last_name':
    case 'emergency_name':
      isValid = isValidName(value);
      break;
    case 'age':
      isValid = isValidAge(value);
      break;
    case 'gender':
      isValid = isValidGender(value);
      break;
    case 'phone_number':
    case 'emergency_phone':
      isValid = isValidPhone(value);
      break;
    case 'team_id':
      isValid = isValidTeamSelection(value);
      break;
    case 'team_token':
      isValid = isValidToken(value);
      break;
    default:
      isValid = value !== '';
  }

  input.classList.toggle('invalid_input', !isValid);
  return isValid;
}

document.addEventListener('DOMContentLoaded', function () {
  const checkbox = document.getElementById('waiverCheckbox');
  const submitButton = document.getElementById('joinTeamButton');
  const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]), select'));

  submitButton.disabled = true;
  submitButton.classList.add('disabled_button');
  checkbox.addEventListener('change', updateSubmitButton);

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
