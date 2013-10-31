class YASGGCrypto
  _salt = undefined
  _key = undefined
  _header_field_bytes = 40

  constructor: (password_hashed) ->
    self = @
    self._key = CryptoJS.enc.Latin1.parse(password_hashed)

  key_get: ->
    @._key

  decrypt: (enrypted_data) ->
    self = @
    encrypted = {}
    encrypted.checksum = CryptoJS.enc.Hex.parse(enrypted_data.substr(_header_field_bytes,
      _header_field_bytes).trim()).toString()
    encrypted.iv = CryptoJS.enc.Hex.parse(enrypted_data.substr(_header_field_bytes * 2, _header_field_bytes).trim())
    encrypted.ciphertext = CryptoJS.enc.Hex.parse(enrypted_data.substr(_header_field_bytes * 3))

    decrypted = {}
    decrypted.data = CryptoJS.AES.decrypt(encrypted, self.key_get(),
      iv: encrypted.iv
      padding: CryptoJS.pad.Pkcs7
      method: CryptoJS.pad.CBC
    )
    decrypted.checksum = encrypted.checksum
    decrypted


exports = this
exports.YASGGCrypto = YASGGCrypto