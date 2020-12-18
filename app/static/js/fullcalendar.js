// The FullCalendar object
var fullCalendarObject = null;

// Local Events Cache
var GCAL_EVENTS_CACHE = {}

document.addEventListener('DOMContentLoaded', function() {
  var Calendar = FullCalendar.Calendar;
  var Draggable = FullCalendar.Draggable;

  var containerEl = document.getElementById('external-events');
  var calendarEl = document.getElementById('calendar');

  // initialize the external events
  // -----------------------------------------------------------------

  new Draggable(containerEl, {
    itemSelector: '.fc-event',
    eventData: function(eventEl) {
      return {
        title: eventEl.innerText,
        id: generateUuid()
      };
    }
  });

  // initialize the calendar
  // -----------------------------------------------------------------

  fullCalendarObject = new Calendar(calendarEl, {
    timeZone: 'Etc/GMT',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    editable: true,
    droppable: true, // this allows things to be dropped onto the calendar
    eventReceive: function(info) {//After event drop
      var event = {
        'id': info.event.id,
        'summary': info.event.title,
        'start': {
            'dateTime': info.event.start.toISOString()
          },
        'end': {
            'dateTime': new Date(info.event.start.getTime() + 60000) //add 1 minute to start date since its empty for now
          }
      };
      GCAL_EVENTS_CACHE[info.event.id] = 1; //Save in cache
      var request = gapi.client.calendar.events.insert({
        'calendarId': 'primary',
        'resource': event
      });
      request.execute(function(event) {
        appendPre('Event created: ' + event.htmlLink);
      });
    },
    eventResize: function(info) {//After event end Date update
      if(info.event.end == null)
        return;

      var event = {
        'start': {
            'dateTime': info.event.start.toISOString()
          },
        'end': {
            'dateTime': info.event.end.toISOString()
          }
      };

      if(info.event.id in GCAL_EVENTS_CACHE){
          var request = gapi.client.calendar.events.patch({
            'calendarId': 'primary',
            'eventId': info.event.id,
            'resource': event
          });
          request.execute(function(event) {
            appendPre('Event updated: ' + event.htmlLink);
          });
      }

    }
  });

  fullCalendarObject.render();

});

// Render Google Calendar Events
function renderGCalEvents(events){
    for (i = 0; i < events.length; i++) {
        var event = events[i];
        renderGCalEvent(event);
    }
}


function renderGCalEvent(gcalEvent){
    if(fullCalendarObject == null){
        return;
    }

    var eventStart = gcalEvent.start.dateTime;
    if (!eventStart)
        eventStart = gcalEvent.start.date;
    var eventEnd = gcalEvent.end.dateTime;
    if (!eventEnd)
        eventEnd = gcalEvent.end.date;
    var eventTitle = gcalEvent.summary;
    var eventId = gcalEvent.id;

    if(eventId in GCAL_EVENTS_CACHE){ //if event has been added, update
        var event = fullCalendarObject.getEventById(eventId);
        if(eventTitle !== event.title)
            event.setProp('title', eventTitle);
        if(eventStart !== event.startStr)
            event.setStart(eventStart);
        if(eventEnd !== event.endStr)
            event.setEnd(eventEnd);
    }
    else{//New event
        fullCalendarObject.addEvent({
            id: eventId,
            title: eventTitle,
            start: eventStart,
            end: eventEnd
        });
        GCAL_EVENTS_CACHE[eventId] = 1; //Save in cache
    }
}

var generateUuid = function (separator) {
    var delim = separator || "";
    function S4() {
        return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
    }
    return (S4() + S4() + delim + S4() + delim + S4() + delim + S4() + delim + S4() + S4() + S4());
};