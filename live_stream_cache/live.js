const { Room } = require("livekit-client");

const wsURL = "wss://mapped-rwo2lxjh.livekit.cloud"
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDUyMDg0NjUsImlzcyI6IkFQSWp6QzJQZmVTYjQyUyIsIm5iZiI6MTcwNTEyMjA2NSwic3ViIjoicXVpY2tzdGFydCB1c2VyIDlhYm5zMSIsInZpZGVvIjp7ImNhblB1Ymxpc2giOnRydWUsImNhblB1Ymxpc2hEYXRhIjp0cnVlLCJjYW5TdWJzY3JpYmUiOnRydWUsInJvb20iOiJxdWlja3N0YXJ0IHJvb20iLCJyb29tSm9pbiI6dHJ1ZX19.dl6Lhyzm4vSLhbF2dGNA-N7gWJJyFZen3WkndkD2zEY"

const room = new Room();
room.connect(wsURL, token);
console.log('connected to room', room.name);

// publish local camera and mic tracks
room.localParticipant.enableCameraAndMicrophone();