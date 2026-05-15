import sdl2
import sdl2.ext
import sdl2.sdlttf
import sdl2.sdlimage
import os

_texture_cache = {}

def draw_image(renderer, path, x, y, w=None, h=None):
    if not path or not os.path.exists(path):
        return
    
    if path in _texture_cache:
        texture = _texture_cache[path]
    else:
        surface = sdl2.sdlimage.IMG_Load(path.encode('utf-8'))
        if not surface:
            return
        texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface)
        sdl2.SDL_FreeSurface(surface)
        if not texture:
            return
        _texture_cache[path] = texture

    if w is None or h is None:
        query_w, query_h = sdl2.Uint32(), sdl2.Uint32()
        sdl2.SDL_QueryTexture(texture, None, None, query_w, query_h)
        w = w or query_w.value
        h = h or query_h.value
        
    rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
    sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, rect)

def render_text(renderer, font, text, x, y, fg_color, center=False, right=False):
    if not text:
        return None
    
    color = sdl2.SDL_Color(fg_color[0], fg_color[1], fg_color[2], 255)
    surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return None

    texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface)
    if texture:
        w, h = surface.contents.w, surface.contents.h
        if center:
            x = x - w // 2
        elif right:
            x = x - w
        rect = sdl2.SDL_Rect(int(x), int(y), w, h)
        sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, rect)
        sdl2.SDL_DestroyTexture(texture)

    sdl2.SDL_FreeSurface(surface)

def render_text_shadow(renderer, font, text, x, y, fg_color, shadow_color=(0,0,0), center=False, right=False, shadow_offset=2):
    if not text: return
    render_text(renderer, font, text, x + shadow_offset, y + shadow_offset, shadow_color, center, right)
    render_text(renderer, font, text, x, y, fg_color, center, right)

def draw_panel(renderer, x, y, w, h, bg_color=(20, 20, 30, 240), border_color=(60, 60, 80)):
    renderer.fill((x, y, w, h), sdl2.ext.Color(*bg_color))
    renderer.draw_rect((x, y, w, h), sdl2.ext.Color(*border_color))
    renderer.draw_rect((x+1, y+1, w-2, h-2), sdl2.ext.Color(40, 40, 50, 100))

def draw_selector(renderer, x, y, w, h, color=(0, 200, 255)):
    renderer.draw_rect((x-2, y-2, w+4, h+4), sdl2.ext.Color(color[0], color[1], color[2], 100))
    renderer.draw_rect((x-1, y-1, w+2, h+2), sdl2.ext.Color(color[0], color[1], color[2], 180))
    renderer.draw_rect((x, y, w, h), sdl2.ext.Color(*color))
    renderer.fill((x, y, w, h), sdl2.ext.Color(color[0], color[1], color[2], 40))

def draw_progress_bar(renderer, x, y, w, h, progress, color=(0, 255, 100), bg_color=(50, 50, 50)):
    renderer.fill((x, y, w, h), sdl2.ext.Color(*bg_color))
    renderer.draw_rect((x, y, w, h), sdl2.ext.Color(20, 20, 20))
    if progress > 0:
        pw = int(w * progress)
        renderer.fill((x+1, y+1, pw-2, h-2), sdl2.ext.Color(*color))
