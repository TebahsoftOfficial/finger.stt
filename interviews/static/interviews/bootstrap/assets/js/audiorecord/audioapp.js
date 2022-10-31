//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var recorder; 						//WebAudioRecorder object
var input; 							//MediaStreamAudioSourceNode  we'll be recording
var encodingType; 					//holds selected encoding for resulting audio (file)
var encodeAfterRecord = true;       // when to encode

// shim for AudioContext when it's not avb.
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext; //new audio context to help us record

//var encodingTypeSelect = document.getElementById("encodingTypeSelect");
//var recordButton = document.getElementById("recordButton");
//var stopButton = document.getElementById("stopButton");
//var submitButton = document.getElementById("rec_submit")
encodingTypeSelect = $('#recdrop #encodingTypeSelect')
recordButton = $('#rec_img')//$('#recdrop #recordButton')
stopButton = $('#recdrop #stopButton')
submitButton = $('#recdrop #rec_submit')
pauseButton = $('#recdrop #pauseButton')

var robj;

//add events to those 2 buttons
//recordButton.addEventListener("click", startRecording);
//stopButton.addEventListener("click", stopRecording);
//submitButton.addEventListener("click", submitRecording);
recordButton.on('click', startRecording);
stopButton.on('click', stopRecording);
submitButton.on('click', submitRecording);
pauseButton.on('click', pauseRecording);

const canvas = document.querySelector('.visualizer');
let audioCtx;
const canvasCtx = canvas.getContext("2d");

var interval;
var rec_time;

function startRecording() {
	console.log("startRecording() called");
	/*
		Simple constraints object, for more advanced features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    var constraints = { audio: true, video:false }

    //recordButton.attr("class","spinner-grow text-danger")
    //recordButton.attr("class","spinner-border")
    //recordButton.attr("role","status")
    recordButton.attr("src","/media/symbol/recording.png")

    $('#recdrop').attr("class","collapse show"); //sujee
    /*
    	We're using the standard promise based getUserMedia()
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/

	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		//__log("getUserMedia() success, stream created, initializing WebAudioRecorder...");

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device

		*/
		audioContext = new AudioContext();

		rec_limit = 7200;
        //console.log($('#user_name').html()+" Logged");
		if( $('#user_name').html() == "tebahsoft3") {
		    console.log("time limit setting ");
		    rec_limit = 6;   // 5min 300
		}

		//update the format
		//document.getElementById("formats").innerHTML="Format: 2 channel "+encodingTypeSelect.options[encodingTypeSelect.selectedIndex].value+" @ "+audioContext.sampleRate/1000+"kHz"

		//assign to gumStream for later use
		gumStream = stream;

		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

        visualize(audioContext, input)
		//stop the input from playing back through the speakers
		//input.connect(audioContext.destination)

		//get the encoding
		//encodingType = encodingTypeSelect.options[encodingTypeSelect.selectedIndex].value;
		encodingType = $('#recdrop #encodingTypeSelect option:selected').val();

		//disable the encoding selector
		//encodingTypeSelect.disabled = true;

		recorder = new WebAudioRecorder(input, {
		  //workerDir: "js/", // must end with slash
		  workerDir: "/media/", // must end with slash
		  encoding: encodingType,
		  numChannels:2, //2 is the default, mp3 encoding supports only 2
		  onEncoderLoading: function(recorder, encoding) {
		    // show "loading encoder..." display
		  //  __log("Loading3 "+encoding+" encoder...");
		  },
		  onEncoderLoaded: function(recorder, encoding) {
		    // hide "loading encoder..." display
		  //  __log(encoding+" encoder loaded");
		  }
		});

		recorder.onComplete = function(recorder, blob) {

            // for time limit stop
            clearInterval(interval);
            recordButton.attr("src","/media/symbol/voice_record.png")
            //stop microphone access
            gumStream.getAudioTracks()[0].stop();
            //disable the stop button
            stopButton.attr("disabled", true);



			//__log("Encoding complete");
			createDownloadLink(blob,recorder.encoding);
			robj = blob;
	        submitButton.attr("disabled",false);
            submitButton.html(`<i class="fas fa-cloud-upload-alt"></i>`);
			//encodingTypeSelect.disabled = false;


		}

		recorder.setOptions({
		  timeLimit:rec_limit,   // 120
		  encodeAfterRecord:encodeAfterRecord,
	      ogg: {quality: 0.5},
	      mp3: {bitRate: 160}
	    });

		//start the recording process
        rec_time = 0;
		interval = setInterval( time_recording, 1000);
		recorder.startRecording();

		// __log("Recording started");

	}).catch(function(err) {
	    console.log("startRec Eroor ");
	  	//enable the record button if getUSerMedia() fails
    	//recordButton.disabled = false;
    	//stopButton.disabled = true;
    	recordButton.attr("disabled", false) ;
    	stopButton.attr("disabled",true);
	});

	//disable the record button
    recordButton.attr("disabled", true);
    stopButton.attr("disabled", false);
    submitButton.attr("disabled", true);
    pauseButton.attr("disabled", false);
}

function time_recording() {
    rec_time = rec_time + 1;
    min = parseInt(rec_time/60);
    str = String(min)+"'"+ String(rec_time%60)+'"';
    $('#time_view').html(str);

}

function stopRecording() {
	clearInterval(interval);
	console.log("stopRecording() called");

    recordButton.attr("src","/media/symbol/voice_record.png")
    submitButton.html('<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>인코딩증');
    //recordButton.removeAttr("class")
    //recordButton.removeAttr("role")

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//disable the stop button
	stopButton.attr("disabled", true);


	//tell the recorder to finish the recording (stop recording + encode the recorded audio)
	recorder.finishRecording();


	recordButton.attr("disabled", false);
	pauseButton.attr("disabled", true);
    pauseButton.attr("pause","false")
    pauseButton.html(`<i class="fas fa-pause"></i>`);
	//__log('Recording stopped');
}

function pauseRecording() {

    if(pauseButton.attr("pause")=="false") {
        recorder.pauseRecording();
        recordButton.attr("src","/media/symbol/pause.png")
        pauseButton.attr("pause","true");
        pauseButton.html(`<i class="fas fa-play"></i>`);
		clearInterval(interval);
    }
    else {
        recorder.resumeRecording();
        recordButton.attr("src","/media/symbol/recording.png")
        pauseButton.attr("pause","false")
        pauseButton.html(`<i class="fas fa-pause"></i>`);
        interval = setInterval( time_recording(), 1000);
    }
}

function visualize(audioCtx, source) {
  /*
  if(!audioCtx) {
    audioCtx = new AudioContext();
  }

  const source = audioCtx.createMediaStreamSource(stream);
  */
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  source.connect(analyser);
  //analyser.connect(audioCtx.destination);

  draw()

  function draw() {
    const WIDTH = canvas.width
    const HEIGHT = canvas.height;

    requestAnimationFrame(draw);

    analyser.getByteTimeDomainData(dataArray);
    canvasCtx.fillStyle = 'rgb(214, 204, 200)'; //sujee
    canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = 'rgb(0, 0, 0)';

    canvasCtx.beginPath();

    let sliceWidth = WIDTH * 1.0 / bufferLength;
    let x = 0;


    for(let i = 0; i < bufferLength; i++) {

      let v = dataArray[i] / 128.0;
      let y = v * HEIGHT/2;    // v * HEIGHT/2;

      if(i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height/2);   // height/2
    canvasCtx.stroke();

  }
}



function createDownloadLink(blob,encoding) {
	var url = URL.createObjectURL(blob);
    $('#recdrop #aid').attr('controls', true)
    $('#recdrop #aid').attr('src', url)
}

function submitRecording(event) {
  event.preventDefault();

  let btn = $(this);
  //   change the button text and disable it
  btn.html("Submitting...").prop("disabled", true).addClass("disable-btn");
  //   create a new File with the recordedData and its name
  const recordedFile = new File([robj], 'audiorecord_'+getCurrentDate()+'.ogg');

    $('#intv_form').attr("style","display");
    $('#recdrop').attr("class","collapse"); //sujee
    let container = new DataTransfer();
    container.items.add(recordedFile);

    $('#rec_duration').html(rec_time);

    document.querySelector('#id_file_upload').files = container.files;
    $('#size_chk').trigger("click");
/*
  //   grabs the value of the language field
  //const title = document.getElementById("rec_title").value;
  const title = $('#recdrop #rec_title').val();
  //   initializes an empty FormData
  let data = new FormData();
  //   appends the recorded file and language value
  data.append("recorded_audio", recordedFile);
  data.append("rec_title", title);
  //   post url endpoint
  const url = "/interviews/record/";
  $.ajax({
    url: url,
    method: "POST",
    data: data,
    dataType: "json",
    success: function (response) {
      if (response.success) {
        submitButton.html = "완료"
      	$('#recdrop').attr('clss','collapse')
        //document.getElementById("alert").style.display = "block";
        window.location.href = response.url //`/interviews/`;
      } else {
        btn.html("Error").prop("disabled", false);
      }
    },
    error: function (error) {
      console.error(error);
    },
    cache: false,
    processData: false,
    contentType: false,
  });
  $('#recdrop').attr("class","collapse");
  */
}


//helper function
function __log(e, data) {
//	log.innerHTML += "\n" + e + " " + (data || '');
}

function getCurrentDate()
{
    var date = new Date();
    var year = date.getFullYear().toString();

    var month = date.getMonth() + 1;
    month = month < 10 ? '0' + month.toString() : month.toString();

    var day = date.getDate();
    day = day < 10 ? '0' + day.toString() : day.toString();

    var hour = date.getHours();
    hour = hour < 10 ? '0' + hour.toString() : hour.toString();

    var minites = date.getMinutes();
    minites = minites < 10 ? '0' + minites.toString() : minites.toString();

    var seconds = date.getSeconds();
    seconds = seconds < 10 ? '0' + seconds.toString() : seconds.toString();

    return year + month + day + hour + minites + seconds;
}