function playAudio() {
    var audio = document.getElementById('audioElement');
    audio.play();
}

function pauseAudio() {
    var audio = document.getElementById('audioElement');
    audio.pause();
}

// I need to implement the logic behind changing the song to the next one on the Queue list
// And for that, I also need to write code to handle Queue lists

function nextSong() {

}

function prevSong() {

}

function recordSong() {

}

// This "stopSong()" function is different than the "pauseAudio()"
// I will implement this functionality by removing the data in the variable named "song_to_stream"
// Then, it will stop showing the Now Playing song from everywhere in the page, and from the audio controls also.

function stopSong() {
    var audio = document.getElementById('audioElement');
    audio.pause();
    audio.currentTime = 0;
}