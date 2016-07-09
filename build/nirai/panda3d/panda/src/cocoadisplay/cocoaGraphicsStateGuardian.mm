// Filename: cocoaGraphicsStateGuardian.mm
// Created by:  rdb (14May12)
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

#include "cocoaGraphicsStateGuardian.h"
#include "config_cocoadisplay.h"
#include "lightReMutexHolder.h"

#include <mach-o/dyld.h>
#import <AppKit/AppKit.h>
#import <OpenGL/CGLRenderers.h>

#ifndef kCGLRendererIDMatchingMask
// For older versions of Mac OS X
#define kCGLRendererIDMatchingMask   0x00FE7F00
#endif

TypeHandle CocoaGraphicsStateGuardian::_type_handle;

////////////////////////////////////////////////////////////////////
//     Function: CocoaGraphicsStateGuardian::Constructor
//       Access: Public
//  Description:
////////////////////////////////////////////////////////////////////
CocoaGraphicsStateGuardian::
CocoaGraphicsStateGuardian(GraphicsEngine *engine, GraphicsPipe *pipe,
                           CocoaGraphicsStateGuardian *share_with) :
  GLGraphicsStateGuardian(engine, pipe)
{
  _share_context = nil;
  _context = nil;

  if (share_with != (CocoaGraphicsStateGuardian *)NULL) {
    _prepared_objects = share_with->get_prepared_objects();
    _share_context = share_with->_context;
  }
}

////////////////////////////////////////////////////////////////////
//     Function: CocoaGraphicsStateGuardian::Destructor
//       Access: Public
//  Description:
////////////////////////////////////////////////////////////////////
CocoaGraphicsStateGuardian::
~CocoaGraphicsStateGuardian() {
  if (_context != nil) {
    [_context clearDrawable];
    [_context release];
  }
}

////////////////////////////////////////////////////////////////////
//     Function: CocoaGraphicsStateGuardian::get_properties
//       Access: Private
//  Description: Gets the FrameBufferProperties to match the
//               indicated config.
////////////////////////////////////////////////////////////////////
void CocoaGraphicsStateGuardian::
get_properties(FrameBufferProperties &properties, NSOpenGLPixelFormat* pixel_format, int screen) {

  properties.clear();

  // Now update our framebuffer_mode and bit depth appropriately.
  GLint double_buffer, stereo, aux_buffers, color_float, color_size,
    alpha_size, depth_size, stencil_size, accum_size, sample_buffers,
    samples, renderer_id, accelerated, window, pbuffer;

  [pixel_format getValues:&double_buffer  forAttribute:NSOpenGLPFADoubleBuffer  forVirtualScreen:screen];
  [pixel_format getValues:&stereo         forAttribute:NSOpenGLPFAStereo        forVirtualScreen:screen];
  [pixel_format getValues:&aux_buffers    forAttribute:NSOpenGLPFAAuxBuffers    forVirtualScreen:screen];
  [pixel_format getValues:&color_float    forAttribute:NSOpenGLPFAColorFloat    forVirtualScreen:screen];
  [pixel_format getValues:&color_size     forAttribute:NSOpenGLPFAColorSize     forVirtualScreen:screen];
  [pixel_format getValues:&alpha_size     forAttribute:NSOpenGLPFAAlphaSize     forVirtualScreen:screen];
  [pixel_format getValues:&depth_size     forAttribute:NSOpenGLPFADepthSize     forVirtualScreen:screen];
  [pixel_format getValues:&stencil_size   forAttribute:NSOpenGLPFAStencilSize   forVirtualScreen:screen];
  [pixel_format getValues:&accum_size     forAttribute:NSOpenGLPFAAccumSize     forVirtualScreen:screen];
  [pixel_format getValues:&sample_buffers forAttribute:NSOpenGLPFASampleBuffers forVirtualScreen:screen];
  [pixel_format getValues:&samples        forAttribute:NSOpenGLPFASamples       forVirtualScreen:screen];
  [pixel_format getValues:&renderer_id    forAttribute:NSOpenGLPFARendererID    forVirtualScreen:screen];
  [pixel_format getValues:&accelerated    forAttribute:NSOpenGLPFAAccelerated   forVirtualScreen:screen];
  [pixel_format getValues:&window         forAttribute:NSOpenGLPFAWindow        forVirtualScreen:screen];
  [pixel_format getValues:&pbuffer        forAttribute:NSOpenGLPFAPixelBuffer   forVirtualScreen:screen];

  properties.set_back_buffers(double_buffer);
  properties.set_stereo(stereo);
  properties.set_rgb_color(1);
  properties.set_float_color(color_float);
  properties.set_color_bits(color_size);
  properties.set_stencil_bits(stencil_size);
  properties.set_depth_bits(depth_size);
  properties.set_alpha_bits(alpha_size);
  properties.set_accum_bits(accum_size);
  if (sample_buffers > 0) {
    properties.set_multisamples(samples);
  }
  //TODO: add aux buffers

  // Extract the renderer ID bits and check if our
  // renderer matches the known software renderers.
  renderer_id &= kCGLRendererIDMatchingMask;
  if (renderer_id == kCGLRendererGenericID ||
      renderer_id == kCGLRendererGenericFloatID ||
      renderer_id == kCGLRendererAppleSWID) {

    properties.set_force_software(1);
  }

  if (accelerated) {
    properties.set_force_hardware(1);
  }
}

////////////////////////////////////////////////////////////////////
//     Function: CocoaGraphicsStateGuardian::choose_pixel_format
//       Access: Private
//  Description: Selects a visual or fbconfig for all the windows
//               and buffers that use this gsg.  Also creates the GL
//               context and obtains the visual.
////////////////////////////////////////////////////////////////////
void CocoaGraphicsStateGuardian::
choose_pixel_format(const FrameBufferProperties &properties,
                    CGDirectDisplayID display,
                    bool need_pbuffer) {

  _context = nil;
  _fbprops.clear();

  // Neither Cocoa nor CGL seem to have a mechanism to query the available
  // pixel formats, unfortunately, so the only thing we can do is ask for
  // one with the properties we have requested.
  pvector<NSOpenGLPixelFormatAttribute> attribs;
  attribs.reserve(15);

  // Picked this up from the pyglet source - seems
  // to be necessary to support RAGE-II, which is not compliant.
  attribs.push_back(NSOpenGLPFAAllRenderers);

  // Don't let it fall back to a different renderer.
  attribs.push_back(NSOpenGLPFANoRecovery);

  // Consider pixel formats with properties equal
  // to or better than we requested.
  attribs.push_back(NSOpenGLPFAMinimumPolicy);

  if (!properties.is_single_buffered()) {
    attribs.push_back(NSOpenGLPFADoubleBuffer);
  }

  if (properties.is_stereo()) {
    attribs.push_back(NSOpenGLPFAStereo);
  }

  int aux_buffers = properties.get_aux_rgba() + properties.get_aux_hrgba() + properties.get_aux_float();
  attribs.push_back(NSOpenGLPFAAuxBuffers);
  attribs.push_back(aux_buffers);
  attribs.push_back(NSOpenGLPFAColorSize);
  attribs.push_back(properties.get_color_bits());
  attribs.push_back(NSOpenGLPFADepthSize);
  attribs.push_back(properties.get_depth_bits());
  attribs.push_back(NSOpenGLPFAStencilSize);
  attribs.push_back(properties.get_stencil_bits());

  // Curious case - if we request anything less than 8 alpha bits,
  // then on some ATI cards, it will grab a pixel format with just
  // 2 alpha bits, which just shows a white window and nothing else.
  // Might have something to do with the compositing window manager.
  // Omitting it altogether seems to make it grab one with 8 bits, though.
  // Dirty hack.  Needs more research.
  if (properties.get_alpha_bits() > 0) {
    attribs.push_back(NSOpenGLPFAAlphaSize);
    attribs.push_back(max(8, properties.get_alpha_bits()));
  }

  if (properties.get_multisamples() > 0) {
    attribs.push_back(NSOpenGLPFASampleBuffers);
    attribs.push_back(1);
    attribs.push_back(NSOpenGLPFASamples);
    attribs.push_back(properties.get_multisamples());
    attribs.push_back(NSOpenGLPFAMultisample);
  }

  if (properties.get_force_software()) {
    // Request the generic software renderer.
    attribs.push_back(NSOpenGLPFARendererID);
    attribs.push_back(kCGLRendererGenericFloatID);
  }

  if (properties.get_force_hardware()) {
    attribs.push_back(NSOpenGLPFAAccelerated);
  }

  attribs.push_back(NSOpenGLPFAWindow);

  if (need_pbuffer) {
    attribs.push_back(NSOpenGLPFAPixelBuffer);
  }

  // Required when going fullscreen, optional when windowed
  attribs.push_back(NSOpenGLPFAScreenMask);
  attribs.push_back(CGDisplayIDToOpenGLDisplayMask(display));

  // End of the array
  attribs.push_back((NSOpenGLPixelFormatAttribute) nil);

  // Create the format.
  NSOpenGLPixelFormat* format = [[NSOpenGLPixelFormat alloc] initWithAttributes:&attribs[0]];
  if (format == nil) {
    cocoadisplay_cat.error() <<
      "Could not find a usable pixel format.\n";
    return;
  }

  // For now, I'm just using the first virtual screen.
  cocoadisplay_cat.debug() <<
    "Pixel format has " << [format numberOfVirtualScreens] << " virtual screens.\n";
  get_properties(_fbprops, format, 0);

  //TODO: print out renderer

  _context = [[NSOpenGLContext alloc] initWithFormat:format shareContext:_share_context];
  [format release];
  if (_context == nil) {
    cocoadisplay_cat.error() <<
      "Failed to create OpenGL context!\n";
    return;
  }

  // Set vsync setting on the context
  GLint swap = sync_video ? 1 : 0;
  [_context setValues:&swap forParameter:NSOpenGLCPSwapInterval];

  cocoadisplay_cat.debug()
    << "Created context " << _context << ": " << _fbprops << "\n";
}

////////////////////////////////////////////////////////////////////
//     Function: CocoaGraphicsStateGuardian::query_gl_version
//       Access: Protected, Virtual
//  Description: Queries the runtime version of OpenGL in use.
////////////////////////////////////////////////////////////////////
void CocoaGraphicsStateGuardian::
query_gl_version() {
  GLGraphicsStateGuardian::query_gl_version();

  // We output to glgsg_cat instead of glxdisplay_cat, since this is
  // where the GL version has been output, and it's nice to see the
  // two of these together.
  if (glgsg_cat.is_debug()) {
    //XXX this is supposed to work, but the NSOpenGLGetVersion
    // symbol cannot be found when I do this

    //GLint major, minor;
    //NSOpenGLGetVersion(&major, &minor);

    //glgsg_cat.debug()
    //  << "NSOpenGLVersion = " << major << "." << minor << "\n";
  }
}

////////////////////////////////////////////////////////////////////
//     Function: CocoaGraphicsStateGuardian::do_get_extension_func
//       Access: Public, Virtual
//  Description: Returns the pointer to the GL extension function with
//               the indicated name.  It is the responsibility of the
//               caller to ensure that the required extension is
//               defined in the OpenGL runtime prior to calling this;
//               it is an error to call this for a function that is
//               not defined.
////////////////////////////////////////////////////////////////////
void *CocoaGraphicsStateGuardian::
do_get_extension_func(const char *name) {
  char* fullname = (char*) malloc(strlen(name) + 2);
  strcpy(fullname + 1, name);
  fullname[0] = '_';

  // Believe it or not, but this is actually the
  // Apple-recommended way to do it.  I know, right?

  if (NSIsSymbolNameDefined(fullname)) {
    NSSymbol symbol = NSLookupAndBindSymbol(fullname);
    free(fullname);
    return (void *) NSAddressOfSymbol(symbol);
  }

  cocoadisplay_cat.warning() <<
    "do_get_extension_func failed for " << fullname << "!\n";

  free(fullname);
  return NULL;
}