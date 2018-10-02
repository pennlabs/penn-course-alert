function getDemandIcon(demand) {
  switch(demand) {
    case 0:
    case 1:
    case 2:
    case 3:
      return '<i style="color: limegreen" data-toggle="tooltip" data-placement="right" title="This course is in low demand" class="fa fa-thermometer-empty" aria-hidden="true"></i>'
    case 4:
    case 5:
    case 6:
    case 7:
      return '<i style="color: orange" data-toggle="tooltip" data-placement="right" title="This course is in medium demand" class="fa fa-thermometer-half" aria-hidden="true"></i>'
    case 8:
    case 9:
    case 10:
      return '<i style="color: orangered" data-toggle="tooltip" data-placement="right" title="This course is in high demand" class="fa fa-thermometer-full" aria-hidden="true"></i>'
  }
}

$(document).ready(function(){
  var courses = new Bloodhound({
    datumTokenizer: Bloodhound.tokenizers.obj.whitespace('section_id'),
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    // prefetch: '/courses'
    remote: {
      url: '/courses?dept=%QUERY',
      wildcard: '%QUERY'
    }
    });

  $('#bloodhound .typeahead').typeahead({
    hint: true,
    highlight: false,
    minLength: 1,
  },
  {
    name: 'states',
    source: courses,
    display: 'section_id',
    templates: {
      empty: '<div class="lmk-rec-element list-group-item">No matching courses found.</div>',
      suggestion: function(data) {
        var instructors = ''
        if(data.instructors.length != 0){ 
          var instructors = data.instructors.join(', ')
        }
        return '<div class="lmk-rec-element list-group-item">' +
          // '<p>' + data.section_id + '</p>' +
          data.section_id + '<br />' +
          '<small>' + data.course_title + '</small>' +
          '<span class="lmk-command-icon">'+getDemandIcon(data.demand)+'</span>' +
          '</div>';
      }
    }
  });
});