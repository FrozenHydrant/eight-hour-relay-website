function openWaiver() {
  document.getElementById('waiverCheckbox').disabled = false;
  window.open('/static/waiver.pdf', '_blank');
}

function updateSubmitButton() {
  const checkbox = document.getElementById('waiverCheckbox');
  const parentCheckbox = document.getElementById('parentCheckbox');
  const submitButton = document.getElementById('joinTeamButton');
  const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]), select'));
  const allFieldsValid = inputs.every(function (input) {
    return validateField(input);
  });

  const parentBlock = document.querySelector('.parent_block');
  const parentBlockVisible = parentBlock && parentBlock.style.display !== 'none';
  const parentCheckboxOk = !parentBlockVisible || (parentCheckbox && parentCheckbox.checked);

  const canSubmit = checkbox.checked && parentCheckboxOk && allFieldsValid;

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

function updateParentBlock() {
  const year = parseInt(document.querySelector('select[name="birthyear"]').value, 10);
  const month = parseInt(document.querySelector('select[name="birthmonth"]').value, 10);
  const day = parseInt(document.querySelector('select[name="birthday"]').value, 10);
  const parentBlock = document.querySelector('.parent_block');

  if (!parentBlock) return;

  if (isNaN(year) || isNaN(month) || isNaN(day)) {
    parentBlock.style.display = 'none';
    return;
  }

  const eventDate = new Date(2026, 8, 12); // September 12, 2026 (month is 0-indexed)
  const birthDate = new Date(year, month - 1, day);
  const ageOnEventDate = new Date(eventDate - birthDate);
  const age = Math.abs(ageOnEventDate.getUTCFullYear() - 1970);

  parentBlock.style.display = age >= 19 ? 'none' : 'flex';
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

  const parentBlock = document.querySelector('.parent_block');
  const parentBlockVisible = parentBlock && parentBlock.style.display !== 'none';

  switch (name) {
    case 'first_name':
    case 'last_name':
    case 'emergency_name':
    case 'parent_name':
    case 'parent_relationship':
      isValid = !parentBlockVisible && (name === 'parent_name' || name === 'parent_relationship')
        ? true
        : isValidName(value);
      break;
    case 'parent_confirm_name': {
      if (!parentBlockVisible) {
        isValid = true;
      } else {
        const parentName = document.querySelector('input[name="parent_name"]');
        isValid = isValidName(value) && parentName && value === parentName.value.trim();
      }
      break;
    }
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
  const parentCheckbox = document.getElementById('parentCheckbox');
  const submitButton = document.getElementById('joinTeamButton');
  const inputs = Array.from(document.querySelectorAll('input:not([type="checkbox"]), select'));

  submitButton.disabled = true;
  submitButton.classList.add('disabled_button');
  checkbox.addEventListener('change', updateSubmitButton);
  if (parentCheckbox) {
    parentCheckbox.addEventListener('change', updateSubmitButton);
  }

  inputs.forEach(function (input) {
    input.addEventListener('input', function () {
      validateField(input);
      // Re-validate parent_confirm_name whenever parent_name changes, and vice versa
      if (input.name === 'parent_name') {
        const confirmInput = document.querySelector('input[name="parent_confirm_name"]');
        if (confirmInput) validateField(confirmInput);
      }
      if (input.name === 'parent_confirm_name') {
        const nameInput = document.querySelector('input[name="parent_name"]');
        if (nameInput) validateField(nameInput);
      }
      updateSubmitButton();
    });
    input.addEventListener('change', function () {
      validateField(input);
      updateSubmitButton();
      if (['birthyear', 'birthmonth', 'birthday'].includes(input.name)) {
        updateParentBlock();
        updateSubmitButton();
      }
    });
  });

  updateSubmitButton();
  updateParentBlock();
});