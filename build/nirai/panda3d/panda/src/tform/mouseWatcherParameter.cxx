// Filename: mouseWatcherParameter.cxx
// Created by:  drose (06Jul01)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) Carnegie Mellon University.  All rights reserved.
//
// All use of this software is subject to the terms of the revised BSD
// license.  You should have received a copy of this license along
// with this source code in a file named "LICENSE."
//
////////////////////////////////////////////////////////////////////

#include "mouseWatcherParameter.h"

////////////////////////////////////////////////////////////////////
//     Function: MouseWatcherParameter::output
//       Access: Published
//  Description: 
////////////////////////////////////////////////////////////////////
void MouseWatcherParameter::
output(ostream &out) const {
  bool output_anything = false;

  if (has_button()) {
    out << _button;
    output_anything = true;
  }

  if (has_keycode()) {
    if (output_anything) {
      out << ", ";
    }
    out << "key" << _keycode;
    output_anything = true;
  }

  if (_mods.is_any_down()) {
    if (output_anything) {
      out << ", ";
    }
    out << _mods;
    output_anything = true;
  }

  if (has_mouse()) {
    if (output_anything) {
      out << ", ";
    }
    out << "(" << _mouse << ")";
    output_anything = true;
  }

  if (is_outside()) {
    if (output_anything) {
      out << ", ";
    }
    out << "outside";
    output_anything = true;
  }

  if (!output_anything) {
    out << "no parameters";
  }
}
