#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. docdeco
    
This provides with a class decorator for docstring documentation.

**About**

*credits*:      `grazzja <jacopo.grazzini@jrc.ec.europa.eu>`_ 

*version*:      1.0
--
*since*:        Fri Jan 27 23:43:03 2017

**Description**

It helps create decorators that apply on any kind of object (class, methods, ...) 
and enable to modify/update, as well as parameterize, the docstring by rewritting 
and reformating (possibly emptying) its :literal:`__doc__` special attribute of 
the considered object (and only this). 
        
See other useful resources at https://wiki.python.org/moin/PythonDecoratorLibrary.

**Contents**
"""


#==============================================================================
# IMPORT STATEMENTS
#==============================================================================

import inspect
import functools
import warnings
import types


try:
    USE_WRAPT_OR_NOT = False # True
    assert USE_WRAPT_OR_NOT
    import wrapt 
except:
    warnings.warn('Module wrapt not imported; see https://github.com/GrahamDumpleton/wrapt')
    pass
        
#==============================================================================
# CLASSES/METHODS
#==============================================================================

class DecoError(Exception):  
    def __init__(self, msg, expr=None):    
        self.msg = msg
        if expr is not None:    self.expr = expr
    def __str__(self):              return repr(self.msg)

class DecoWarning(Warning):   
    def __init__(self, msg, expr=None):    
        self.msg = msg
        if expr is not None:    self.expr = expr
    def __str__(self):              return repr(self.msg)
    def __repr__(self):             return repr(self.msg)

class Docstring(object):
    """A bunch of docstrings classes, metaclasses and methods decorators.
    """

    #/************************************************************************/
    @classmethod
    def _format_obj(cls, **kwargs):
        """Create a decorator that applies on any kind of object and returns an 
        updated docstring through rewritting/reformating (possibly emptying) of 
        the :literal:`__doc__` special attribute of the considered object.
        
            >>> doc_rebuilder = Docstring._format_obj(**kwargs)
            
        Keyword Arguments
        -----------------
        kwargs : dict
            strings too look for and replace in the docstring documentation of 
            the considered object; if :literal:`_VOID_` is passed as :literal:`True`, 
            an empty string is returned.
            
        Returns
        -------
        doc_rebuilder : function
            a function that returns a string.
            
        Example
        -------
        >>> class DummyClass(object):
        ...     \"\"\"A {quality_doc} documentation for a {quality_class} class.\"\"\"
        ...     def dummy_method():
        ...         \"\"\"{x} documentation, like his father {y}.\"\"\"
        ...         return   
        >>> print Docstring._format_obj(quality_doc:'dummy',quality_class='useless')(DummyClass)   
            A dummy documentation for a useless class.
        >>> print Docstring._format_obj(**{'x':'Dummy', 'y':DummyClass.__name__})(DummyClass.dummy_method)     
            Dummy documentation, like his father DummyClass.
        >>> Docstring._format_obj(_VOID_=True)(DummyClass)
            ''
        """
        def doc_rebuilder(obj):
            if kwargs.pop('_VOID_',False):
                return ''
            try:
                doc = getattr(obj,'__doc__')
                assert doc
            except:
                return ''
            else:
                return doc.format(**kwargs) # str(doc).format(**kwargs)
        return doc_rebuilder
            
    #/************************************************************************/
    @classmethod
    def format_method(cls, **kwargs):
        """Create a decorator that enables to parameterize the docstring of a 
        method by rewritting and reformating (possibly emptying) its :literal:`__doc__` 
        special attribute (and only this).       
            
            >>> new_func = Docstring.format_method(**kwargs)(func)
    
        Example
        ------- 
        Let's consider a dummy function whose documentation will be decorated:
        
        >>> def dummy_method():
        ...     \"\"\"A certainly {quality} documentation.\"\"\"
        ...     return            
        
        We can then adapt this 'base' function:
        
        >>> useless_method = Docstring.format_method(quality='useless')(dummy_method)
        >>> print useless_method.__doc__
            A certainly useless documentation.
        >>> useful_method = Docstring.format_method(quality='useful')(dummy_method)
        >>> print useful_method.__doc__
            A certainly useful documentation.
            
        We can even 'empty' the documentation using the :literal:`_VOID_` keyword:

        >>> empty_method = Docstring.format_method(_VOID_=True)(dummy_method)
        >>> empty_method.__doc__
            ''                
            
        Note that, as it is, the docstring of the base function looks rather 
        irrelevant:
        
        >>> print dummy_method.__doc__
            A certainly {quality} documentation.
        
        In particular :literal:`staticmethod` and :literal:`classmethod` objects 
        are also supported (i.e. instance methods as well as normal functions) 
        thanks to the :mod:`wrapt` module and the :class:`FunctionWrapper` class 
        therein::
            
            class A(object):
            
                @Docstring.format_method(quality='static')
                @staticmethod
                def decorated_static_method():
                    \"\"\"A {quality} method documentation.\"\"\"
                    return            
            
                @Docstring.format_class(quality='class')
                @classmethod
                def decorated_class_method():
                    \"\"\"A {quality} method documentation.\"\"\"
                    return            
        
        where the decorator is inserted prior to the method closure definition
        (special decorators :literal:`@staticmethod` and :literal:`@classmethod`).
        Therefore, the methods are decorated as expected:
        
            >>> print A.decorated_static_method.__doc__
                A static method documentation.
            >>> A.decorated_class_method.__doc__
                A class method documentation.
        
        See also
        --------
        :meth:`format_class`
        """   
        _doc_formatter = cls._format_obj(**kwargs)                       
        ## using functools.wraps: this will work but the method type of any bounded
        ## function (static, instance or class method) is also altered
        #def _func_decorator(func):
        #    new_func = functools.wraps(func)(func)
        #    new_func.__doc__ = _doc_formatter(func)
        #    return new_func
        try:
            assert USE_WRAPT_OR_NOT and wrapt
        except:   
            class _func_decorator(__MethodDecorator):
                def __init__(self, func, obj=None, cls=None, method_type='function'):
                    #super(_func_decorator,self).__init__(func, obj=obj, cls=cls, method_type=method_type)
                    __MethodDecorator.__init__(self, func, obj=obj, cls=cls, method_type=method_type)
                    # we had one attribute wrt. a standard method_decorator instance
                    setattr(self,'__doc__',_doc_formatter(self.func))
                def __getattribute__(self, attr_name): 
                    # we ensure that the docstring which is the __doc__ attribute of the
                    # decorator, not that of the function itself
                    if attr_name in ('__doc__',):
                        return object.__getattribute__(self, attr_name) 
                    # otherwise behaves like the superclass class
                    #return super(_func_decorator,self).__getattribute__(attr_name)
                    return __MethodDecorator.__getattribute__(self, attr_name)
        else:
            def _func_decorator(func):
                #@my_wrapper
                #def new_func(*_args, **_kwargs):
                #   return func(*_args, **_kwargs)
                new_func = method_decorator(func)
                #new_func = method_wrapper(func)
                # now we update the '__doc__' by recycling the doc already commited in 
                # the FunctionWrapper object new_func: this enables avoiding issues when
                # dealing with classmethod or staticmethod methods:
                #    "AttributeError: 'classmethod' object attribute '__doc__' is read-only"
                try:    # write on the wrapper...
                    new_func.__doc__ = _doc_formatter(new_func)
                except: 
                    # still, we allow this type of error, as it may occur in the case the
                    # order of closures was not well set, e.g. by implementing:
                    #    @classmethod
                    #    @Docstring.format_class(**kwargs)
                    # instead of:
                    #    @Docstring.format_class(**kwargs)
                    #    @classmethod
                    pass
                return new_func
        return _func_decorator

    #/************************************************************************/
    @classmethod
    def format_class(cls, **kwargs):           
        """Create a  decorator that enables to parameterize the docstring of a 
        class by rewritting and reformating (possibly emptying) its :literal:`__doc__` 
        special attribute (and only this).  
        
            >>> new_cls = Docstring.format_class(**kwargs)(cls)
    
        Examples
        -------- 
        Let's consider a dummy function whose documentation will be decorated:
        
        >>> class dummy_class(object):
        ...     \"\"\"A certainly {quality} documentation.\"\"\"
        ...     pass            
                
        >>> useless_class = Docstring.format_class(quality='useless')(dummy_class)
        >>> print useless_class.__name__
            dummy_class
        >>> print useless_class.__doc__
            A certainly useless documentation.                
            
        However, in the case an :literal:`empty` keyword is passed, the docstring 
        will be emptied (even in the case other keyword arguments are present)
        
        >>> empty_class = Docstring.format_class(VOID=True)(dummy_class)
        >>> empty_class.__doc__
            ''
        >>> empty_class = Docstring.format_class(quality='useless', VOID=True)(dummy_class)
        >>> empty_class.__doc__
            ''
            
        See also
        --------
        :meth:`format_method`
        """     
        _doc_formatter = cls._format_obj(**kwargs)                       
        try:
            assert USE_WRAPT_OR_NOT and wrapt
            warnings.warn('wrapt based class decorator not implemented')
        except:
            pass
        finally:
            def _class_decorator(_cls):
                try: 
                    meta_cls = _cls.__metaclass__
                except:
                    meta_cls = type
                class metaclass_decorator(meta_cls):
                    def __new__(meta, name, bases, attrs):
                        name = _cls.__name__
                        attrs = _cls.__dict__
                        bases = _cls.__bases__
                        return meta_cls.__new__(meta, name, bases, attrs)
                metaclass_decorator.__name__ = '__metaclass__'
                class new_cls(_cls):
                    __metadata__ = metaclass_decorator
                    # We set the __doc__ directly when defining the new class, as to avoid the
                    # 'non-writable' issue with __doc__
                    # indeed attribute '__doc__' of 'type' objects is not writable:
                    #    "AttributeError: attribute '__doc__' of 'type' objects is not writable"
                    # hence new-style classes (child of 'object' type) have non writable docstring
                    __doc__ = _doc_formatter(_cls)
                    # override new_cls.__init__ to prevent recursion, because new_cls.__init__ 
                    # is _cls.__init__ and it keeps calling itself.
                # name set after the class declaration
                try:
                    new_cls.__name__ = _cls.__name__
                except: pass
                try:
                    new_cls.__module__ = _cls.__module__
                except: pass
                return new_cls
        return _class_decorator

    #/************************************************************************/
    @classmethod
    def format(cls, **kwargs):
        """Universal decorator that enables to parameterize the docstring of any 
        method or class by rewritting and reformating (possibly emptying) its 
        :literal:`__doc__` special attribute (and only this).  
            
            >>> new_obj = Docstring.format(**kwargs)(obj)
    
        Examples
        -------- 
        The format conversion method can be applied indifferently over classes 
        or methods:
        
        >>> class dummy_class(object):
        ...     \"\"\"A certainly {quality} documentation.\"\"\"
        ...     pass            
        >>> useful_class = Docstring.format(quality='useful')(dummy_class)
        >>> print useful_class.__doc__
            A certainly useful documentation.
        >>> def dummy_method():
        ...     \"\"\"A certainly {quality} documentation.\"\"\"
        ...     return            
        >>> useless_method = Docstring.format(quality='useless')(dummy_method)
        >>> print useless_method.__doc__
            A certainly useless documentation.
      
        Note
        ----
        Mostly a copy/paste of :meth:`format_method` and :meth:`format_class` 
        methods.
      
        See also
        --------
        :meth:`format_method`, :meth:`format_class`        
        """
        def _decorator(obj):
            if inspect.isclass(obj):
                _class_decorator = cls.format_class(**kwargs)                       
                return _class_decorator(obj)
            else:
                _func_decorator = cls.format_method(**kwargs)                       
                return _func_decorator(obj)
        return _decorator
        
    #/************************************************************************/
    @classmethod
    def decorate(cls, attr_names=None, **kwargs):
        """Universal decorator that enables to parameterize the docstring of any
        class by rewritting and reformating (possibly emptying) the :literal:`__doc__` 
        special attributes (and only this) of all its members.  
            
            >>> new_cls = Docstring.decorate(attr_names=None, **kwargs)(cls)
    
        Examples
        --------
         
        Note
        ----
        Inside this project, we also use the :meth:`decorate` method to decorate, 
        through the special attribute :literal:`__metaclass__`, all methods 
        inherited from :data:`base` classes, namely::
        
            class Base(object):
                def dummy_method_from_Base():
                    \"\"\"A certainly {quality} documentation that is decorated.\"\"\"
                    return
                    
            class Derived(Base):
                @Docstring.decorate(Base.__dict__.keys(),quality='useful')
                class __metaclass__(type): pass
                def dummy_method_from_Derived():
                    \"\"\"A certainly {quality} documentation that is left as it is.\"\"\"
                    return            
                
        as indeed, this way, the methods inherited from :class:`Base`, and those 
        only, are decorated:
        
        >>> print Derived.dummy_method_from_Derived.__doc__ # not decorated
            A certainly {quality} documentation that is left as it is.
        >>> print Derived.dummy_method_from_Base.__doc__
            A certainly useful documentation that is decorated.
        """
        if attr_names is None:
            attr_names = ()
        elif not isinstance(attr_names,(list,tuple)):
            raise DecoError('type {} not accepted for list/tuple of decorated members'.format(type(attr_names)))
        # various local objects
        obj_decorator = cls._format_obj(**kwargs)#analysis:ignore
        format_decorator = cls.format(**kwargs)#analysis:ignore
        str_format = lambda s: s.format(**kwargs) if s is not None else ''                   
        special_members = ['__metaclass__','__module__','__weakref__','__dict__','__class__']#analysis:ignore
        def decorator(obj, obj_name=None):
             # deal with special '__doc__' member
            if obj_name=='__doc__':
                try:    
                    return str_format(obj)
                except:  return obj or ''
            # don't consider other special members and other special members unless 
            # it is explicitely to decorate them (e.g. __init__)
            elif obj_name in special_members:                               \
                # or (obj_name.startswith('__') and obj_name.endswith('__') and obj_name not in attr_names):
                return obj
            # deal with properties
            elif isinstance(obj, property):                 
                try:   
                    return property(obj.__get__, obj.__set__, obj.__delattr__, str_format(obj.__doc__))
                except:  return obj # e.g. property not decorated
            # deal with class members
            elif inspect.isclass(obj):
                try: 
                    return cls.format_class(**kwargs)(obj) 
                except: return obj
            # deal with method members
            elif inspect.isroutine(obj): # inspect.ismethod(obj):
                try: 
                    return  cls.format_method(**kwargs)(obj) 
                except: return obj
            ## deal with attribute members
            else: 
                try: # whenever __doc__ is writeable
                    obj.__doc__ = obj_decorator(obj)
                    return obj
                except: 
                    return obj
        return class_decorator(decorator, *attr_names)

        
