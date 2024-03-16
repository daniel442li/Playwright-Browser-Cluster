console.log('Content Script!!');

document.addEventListener('click', function(e) {
    console.log('Click event:', e);
    const dot = document.createElement('div');
    dot.style.position = 'absolute';
    dot.style.width = '10px';
    dot.style.height = '10px';
    dot.style.backgroundColor = 'red';
    dot.style.borderRadius = '50%';
    dot.style.pointerEvents = 'none'; // Ensure the dot does not interfere with other interactions
    dot.style.left = `${e.pageX - 5}px`; // Center the dot on the cursor
    dot.style.top = `${e.pageY - 5}px`; // Adjust so the center of the dot matches the click point
    dot.style.zIndex = '999999'; // Set a high z-index value to ensure it appears above everything

    document.body.appendChild(dot);

    // Fade out the dot
    let opacity = 1;
    const fadeInterval = setInterval(function() {
      if (opacity <= 0.1) {
        clearInterval(fadeInterval);
        document.body.removeChild(dot);
      }
      dot.style.opacity = opacity;
      opacity -= opacity * 0.1;
    }, 50);

    // console.log('Element Clicked: HTML -', e.target.innerHTML);
    // console.log('Element Clicked: Outer HTML -', e.target.outerHTML);
    // console.log('Element Clicked: Name -', e.target.name);
    // console.log('Element Clicked: Value -', e.target.value);
    // console.log('Element Clicked: Type -', e.target.type);
    // console.log('Element Clicked: Text -', e.target.innerText);
    // console.log('Element Clicked: Attributes -', e.target.attributes);
    // console.log('Element Clicked: Classes -', Array.from(e.target.classList));
    // console.log('Element Clicked: Styles -', e.target.style.cssText);
    // console.log('Click Position: X -', e.pageX, 'Y -', e.pageY);
    // console.log('Click Position relative to viewport: X -', e.clientX, 'Y -', e.clientY);

  //   let element = e.target;
  //   while (element) {
  //     console.log('Element:', element.tagName);
  //     if (element.tagName === 'BUTTON' || (element.tagName === 'INPUT' && ['text', 'password', 'email', 'search'].includes(element.type))) {
  //         console.log('Button or text input clicked: ', element);
          
  //         // Your existing logging here...
  
  //         break;
  //     }
  //     element = element.parentElement;
  // }

    

  //   if (e.target.tagName === 'BUTTON') {
  //     let selector = e.target.id ? `#${e.target.id}` :
  //                    e.target.className ? `.${e.target.className.split(' ')[0]}` : 
  //                    'button';
  //     chrome.runtime.sendMessage({type: 'buttonClicked', selector: selector});
  //   }

});


document.addEventListener('mousedown', function(e) {
  var element = e.target; // Element that was clicked.
  
  console.log('Element tag:', element.tagName); // Gives the tag of the element.
  console.log('Element class:', element.className); // Gives the class of the element.
  console.log('Element id:', element.id); // Gives the id of the element.
  console.log('Element name:', element.name); // Gives the name of the element.
  console.log('Element value:', element.value); // Gives the value of the element.
  console.log('Element attributes:', element.attributes); // Gives list of all attributes of the element.
  console.log('HTML of the element:', element.outerHTML); // Gives the complete HTML of the element.
});