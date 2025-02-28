var source = new EventSource('http://192.168.1.90/events');

source.addEventListener('open', function (message) {
  console.log('created connection');
});

source.addEventListener('error', function (message) {
  console.error(message);
});

source.addEventListener('message', function (message) {
  console.log(message.data);
});

source.addEventListener('sensors', function (message) {
  console.log(JSON.parse(message.data).temperature);
});

source.addEventListener('close', function (message) {
  console.log('connection closed');
});

let button = document.querySelector('button');

if (button) {
  button.addEventListener('click', function () {
    console.log('closing connection');
    source.close();
  });
}
