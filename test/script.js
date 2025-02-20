var source = new EventSource('http://192.168.0.106/events');

source.addEventListener('message', function (message) {
  console.log(message.data);
});

// source.addEventListener('error', function (message) {
//   console.error(message);
// });

source.addEventListener('sensors', function (message) {
  console.log(JSON.parse(message.data).temperature);
});

// source.addEventListener('close', function (message) {
//   console.log(message);
// });

let button = document.querySelector('button');

if (button) {
  button.addEventListener('click', function () {
    console.log('closing connection');
    source.close();
  });
}

console.log('created connection');