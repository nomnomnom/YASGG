$ = jQuery

class Fullscreen
  _fullscreen_hint_sel = '#js-fullscreen-hint'

  constructor: ->
    if screenfull.enabled
      $(_fullscreen_hint_sel).show ->
        $(document).bind 'keypress', (e) ->

          # toggle if no input elm has focus
          # bind fullscreen toggle to f key
          code = ((if e.keyCode then e.keyCode else e.which))
          # f or F key
          screenfull.toggle() if not $('input').is(':focus') and (code is 70 or code is 102)

exports = this
exports.Fullscreen = Fullscreen