Inteco
======

This module allows the instance initialization for the company
"Inteco", also allows the installation of new modules
testing the features added on runbot.

To find the repositories needed for this module please review the
oca_dependencies.txt file.

Just declare all the repositories on 10.0 branches in your addons-path
and install "inteco" module.

Herencia a Usuarios  
===================
Cuando se crea un usuario sin socio y ya existe un socio con el mismo correo electrónico, asigna el socio automáticamente. Esto permite evitar errores al crear un nuevo usuario desde el sitio web que ya tiene un socio registrado, y el sistema intenta crear un nuevo socio con el mismo correo electrónico.  

Esto no lo hace Odoo porque, de forma predeterminada, podría haber más de un socio con el mismo correo electrónico, por lo que tal caso no sucedería.


**Nota de archivo phone_validation_mixin**
==========================================  
El archivo fue modificado a la version 14 esta es la nota que tenia el archivo

In order to properly shown the corresponding warning message when an
exception is raised trying to parse a phone number it was necessary to
add the raise_exception parameter that was previously removed in
odoo/addons/phone_validation/models/phone_validation_mixin.py:21

@param raise_exception: For this a new parameter is added in this
method, this does not affect calls in other codes
