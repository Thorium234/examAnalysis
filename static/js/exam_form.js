django.jQuery(document).ready(function($) {
    // Function to ensure only one exam type is selected
    function handleExamTypeSelection(clickedCheckbox) {
        $('.exam-type-checkbox').not(clickedCheckbox).prop('checked', false);
    }
    
    // Add click handler to exam type checkboxes
    $('.exam-type-checkbox').click(function() {
        handleExamTypeSelection(this);
    });
    
    // Validation before form submission
    $('form').submit(function(e) {
        // Check if at least one exam type is selected
        if (!$('.exam-type-checkbox:checked').length) {
            alert('Please select one exam type.');
            e.preventDefault();
            return false;
        }
        
        // Check if at least one form is selected
        if (!$('input[name="participating_forms"]:checked').length) {
            alert('Please select at least one participating form.');
            e.preventDefault();
            return false;
        }
        
        return true;
    });
});