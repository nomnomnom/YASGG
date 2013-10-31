$ = jQuery

class Gallery
  _content_sel = '#content'
  _thumbnail_sel = '.thumbnail-container'
  _password_dialog_sel = '#password-dialog'
  _password_input_sel = '#js-password-input'
  _password_submit_sel = '#js-password-submit'
  _lightbox_open_sel = '.lightbox'
  _lightbox_close_sel = '.lightbox-close'
  _thumbnail_enrypted_sel = '.thumbnail-img.encrypted'
  _key_cookie_name = 'yasgg_crypto_key'
  _is_image_grid_initialized = false
  _use_crypto = false
  _crypto = undefined

  constructor: ->
    self = @
    body = $('body:first')

    self._init_lightbox()

    if body.attr('data-use-crypto')
      self._use_crypto = true

    if self._use_crypto
      # open password dialog if no password is set
      # else decrypt thumbnail images
      key = self.key_get()
      if key
        self._crypto = new YASGGCrypto(key)
        if self._decrypt_thumbnails() is true
          self._handle_initial_request()
      else
        self._init_password_dialog()
    else
      self._handle_initial_request()
      self._init_image_grid()

  password_set: (password) ->
    if password
      $.cookie(_key_cookie_name, CryptoJS.MD5(password).toString())
    else
      $.removeCookie(_key_cookie_name)

  key_get: ->
    $.cookie(_key_cookie_name)

  _handle_initial_request: ->
    # open image in lightbox if given
    hash_components = window.location.hash.split '#'
    if hash_components.length > 1 and $.isNumeric(hash_components[1])
      $(_lightbox_open_sel + ':eq(' + hash_components[1] + ')').click()

  _init_image_grid: ->
    self = @
    self._is_image_grid_initialized = true
    $(_content_sel).isotope
      itemSelector: _thumbnail_sel
      layoutMode: 'fitRows'

  _init_password_dialog: ->
    self = @

    $.magnificPopup.open
      items:
        src: $(_password_dialog_sel)
        type: 'inline'
      showCloseBtn: false
      midClick: false
      enableEscapeKey: false
      closeOnBgClick: false

    $(_password_submit_sel).click ->
      password_input = $(_password_input_sel)
      password = password_input.val()
      if not password
        return

      initial_submit_text = $(_password_submit_sel).html()
      $(_password_submit_sel).html('checking password...').attr('disabled', 'disabled')
      $(_password_input_sel).attr('disabled', 'disabled')

      self.password_set(password)
      self._crypto = new YASGGCrypto(self.key_get())

      $(_password_submit_sel).html(initial_submit_text).removeAttr('disabled')
      $(_password_input_sel).removeAttr('disabled')
      self._decrypt_thumbnails()
      password_input.val('')

    $(document).on 'keypress', _password_input_sel, (e) ->
      code = ((if e.keyCode then e.keyCode else e.which))
      if code == 13  # on enter key
        $(_password_submit_sel).click()

  _init_lightbox: ->
    self = @

    $(_lightbox_open_sel).magnificPopup
      type: 'image'
      showCloseBtn: false
      gallery:
        preload: [1, 1]
        enabled: true
        navigateByImgClick: true
        arrowMarkup: '<button title=\'%title%\' type=\'button\' class=\'mfp-arrow mfp-arrow-%dir%\'></button>'
        tPrev: 'Previous (Left arrow key)'
        tNext: 'Next (Right arrow key)'
        tCounter: '%curr% of %total% &nbsp;&nbsp;<button class=\'lightbox-close\' type=\'button\' title=\'Close (Esc)\'> × </button>'
      callbacks:
        elementParse: (item) ->
          img = item.el
          if !img.hasClass('encrypted')
            return
          $.ajax(
            type: 'GET',
            url: img.attr('data-src-encrypted'),
            async: false
          ).done (data) ->
            self._decrypt_image(img, data, 'href')
            item.src = img.attr('href')
            img.removeClass('encrypted')
        imageLoadComplete: ->
          mp = $.magnificPopup.instance

          # set history hash
          window.location = '#' + mp.index

          # swipe stuff
          $('.mfp-img').on('swipeleft',->
            mp.next()
          ).on('swiperight', (e) ->
            mp.prev()
          )
        close: ->
          # reset history hash
          window.location = '#'

    $(document).on 'click', _lightbox_close_sel, ->
      $.magnificPopup.close()

  _decrypt_image: (img, data, target_attr, check_password) ->
    self = @

    decrypted = self._crypto.decrypt(data)
    if check_password
      # password wrong
      if decrypted.checksum != CryptoJS.SHA1(decrypted.data.toString()).toString()
        return false
    img.attr target_attr, 'data:image/jpeg;base64,' + decrypted.data.toString(CryptoJS.enc.Base64)
    img.removeClass('loading').removeClass('encrypted')
    return img

  _decrypt_thumbnails: ->
    self = @
    password_wrong_rumble = undefined
    password_ok = true
    images_to_decrypt_count = $(_thumbnail_enrypted_sel).length
    images_decrypted_count = 1

    # load the first image synchronous and check the password, if the password is ok, load the other images async
    first_image = $(_thumbnail_enrypted_sel + ':first')
    $.ajax(
      type: 'GET'
      url: first_image.attr('data-src-encrypted')
      async: false
    ).done (data) ->
      if self._decrypt_image(first_image, data, 'src', true)
        $.magnificPopup.close()
        $(_thumbnail_enrypted_sel).each ->
          img = $(@)
          $.ajax(
            type: 'GET'
            url: img.attr('data-src-encrypted')
            async: true
          ).done (data) ->
            self._decrypt_image(img, data, 'src')
            images_decrypted_count++
            if not self._is_image_grid_initialized and images_decrypted_count >= images_to_decrypt_count
              self._init_image_grid()
      else
        self.password_set(null)
        password_ok = false

        $(_password_dialog_sel).jrumble
          x: 40
          y: 0
          rotation: 0
        clearTimeout password_wrong_rumble
        $(_password_dialog_sel).trigger "startRumble"
        password_wrong_rumble = setTimeout(->
          $(_password_dialog_sel).trigger "stopRumble"
        , 300)

    return password_ok


exports = this
exports.Gallery = Gallery