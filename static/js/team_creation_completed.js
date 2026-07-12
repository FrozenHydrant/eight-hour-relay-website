// https://stackoverflow.com/questions/77817071/how-to-assign-copy-to-clipboard-button-to-specific-text-html-javascript
function copy_to_clipboard(elm_id) {
    var text = document.getElementById(elm_id).innerHTML;
    navigator.clipboard.writeText(text);
}