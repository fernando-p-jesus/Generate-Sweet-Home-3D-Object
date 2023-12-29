
#import argparse
import math
import yaml
#from os.path import exists

from enum import Enum

# For reference, I used the following reference to prepresent the 3d
# space. This might not be the same standard reference used by
# vizualization software... it was what I initialy adopted and later
# realized I could be wrong, but I had already to many things working
# that I decided to not touch it. The impact of this is that objects
# will appear on their side, but since they can be rotated it is not a
# big issue.
#
#               | z
#        (x,z)  |
#           L   |
#           E   |   (y,z) BACK
#           F   |
#           T   |
#               |               y
#               *-----------------
#              /
#             /   (x,y) BOTTOM
#            /
#           / x
#
class furniture:
    def __init__(self, objectName, width, depth, height \
                     , thickness=1.5, x0=0, y0=0, z0=0, openTop=False \
                     , materialsFileName=None, rimMaterial=None, interiorMaterial=None \
                     , exteriorMaterial=None, shelveMaterial=None, frontMaterial=None):
        self.objectName = objectName
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.depth = depth
        self.width = width
        self.height = height
        self.thickness = thickness
        self.openTop = openTop

        self.materialsFileName = materialsFileName
        self.rimMaterial = rimMaterial
        self.interiorMaterial = interiorMaterial
        self.exteriorMaterial = exteriorMaterial
        self.shelveMaterial = shelveMaterial
        self.frontMaterial = frontMaterial

        self.shelves = []
        self.fronts = []
        self.back = {}

    # Shelves should be represented by a class... but having a class
    # for shelves alone would be a bit strange. The right way would be
    # to have a class to represent any part of the object (including
    # the outer frame, back and front), but I had already the outer
    # frame working, so I decided to leave it this way.
    #
    # Stores information to build a shelve
    # Shelves are perpendicular to (y,z) but the may not be paralel to (x,y)
    # * Arguments:
    #   z1 - the height where the shelve intercepts the left side
    #   z1 - the height where the shelve intercepts the right side (=z1 if z2 is omited)
    #   rimMtl - material to be used on the shelve rim
    #   slvMtl - material to be used on the shelve bottom and top sides
    # * Defaults
    #   z1 - mandatory
    #   z2 defaults to z1
    #   rimMaterial and shelveMaterial default to the corresponding object materials
    # * TODO - we could have different materials for the top and bottom
    def addShelve(self, z1, z2=None, startDepth=None, endDepth=None, thickness=None \
                      , shelveName=None, rimMaterial=None, shelveMaterial=None):
        if shelveName is None: shelveName = "Shelve %d" %(len(self.shelves)+1)
        self.shelves.append({"z1": z1, "z2" : z2, "startDepth" : startDepth, "endDepth" : endDepth \
                            , "thickness" : thickness, "shelveName" : shelveName\
                            , "rimMaterial" : rimMaterial, "shelveMaterial" : shelveMaterial})

    # See first comment on the addShelves member
    #
    # Stores information to build a front part. Several fronts (doors)
    # can be speciffied. fronts will be placed at the front of the object (y=y0+depth).
    # By specifying the appropriate arguments, you can build multiple
    # fronts.  For instance you can build cabinet with two doors on
    # the lower part (half the cabinet width each) and a single door
    # on the upper side.
    #
    # * Arguments
    #   x1, z1 - specify the lower left corner of the front - default to self.x0, self.z0
    #   width, height the size of the front - default to the same self.* attributes
    #   sizeCorrection (sc) - this allows you to specify a front that will be
    #          larger or smaller than the specified dimensions. Actual front
    #          position will be (x1+sc, z1+sc) and size will be (width+2*sc, height+2*sc).
    #   frontMaterial default to the corresponding object material
    def addFront(self, y=None, z=None, width=None, height=None, frontName=None, sizeCorrection=0, frontMaterial=None):
        if frontName is None: frontName = "Front %d" %(len(self.fronts)+1)
        self.fronts.append({"y" : y, "z" : z, "width": width, "height" : height, "frontName" : frontName\
                            , "sizeCorrection" : sizeCorrection, "frontMaterial" : frontMaterial})

    # See first comment on the addShelves member
    #
    # Stores information to build the back part.
    # * Arguments
    #   Back and front materials. Defaults to Objetc exterior/interior materials
    def addBack(self, backMaterial=None, frontMaterial=None):
        self.back = {"backMaterial" : backMaterial, "frontMaterial" : frontMaterial}

    def __auxMtlName(self, mtl):
        if mtl is None or mtl == '':
            return("")
        else:
            return("usemtl %s\n" %(mtl))

    def __auxVertice(self, x, z, y):
        return("v %f %f %f\n" %(x, z, y))

    # TODO - no caso de ser openTop, as junções do topo têm de ser até ao topo
    def __buildOuterVertices(self):
        # We use alternate variables for code clarity
        x0 = self.x0
        y0 = self.y0
        z0 = self.z0
        d = self.depth
        w = self.width
        h = self.height
        t = self.thickness
        # We start by specifying the vertices. We do this by creating
        # the points where vertical and horizontal frames join:
        tmpV1 = "g Lower left union\n"					   +\
                self.__auxVertice(x0, z0        , y0)      +\
                self.__auxVertice(x0, z0 + h    , y0)      +\
                self.__auxVertice(x0, z0 + h - (0 if self.openTop else t), y0 + t)  +\
                self.__auxVertice(x0, z0 + t    , y0 + t)
        tmpV2 = "g Uper left union\n"						   +\
                self.__auxVertice(x0 + d, z0        , y0)      +\
                self.__auxVertice(x0 + d, z0 + h    , y0)      +\
                self.__auxVertice(x0 + d, z0 + h - (0 if self.openTop else t), y0 + t)  +\
                self.__auxVertice(x0 + d, z0 + t    , y0 + t)
        tmpV3 = "g Uper right union\n"							   +\
                self.__auxVertice(x0    , z0 + h - (0 if self.openTop else t), y0 + w - t)  +\
                self.__auxVertice(x0    , z0 + h    , y0 + w)      +\
                self.__auxVertice(x0 + d, z0 + h    , y0 + w)      +\
                self.__auxVertice(x0 + d, z0 + h - (0 if self.openTop else t), y0 + w - t)
        tmpV4 = "g Lower right union\n"						   +\
                self.__auxVertice(x0    , z0    , y0 + w)      +\
                self.__auxVertice(x0    , z0 + t, y0 + w - t)  +\
                self.__auxVertice(x0 + d, z0 + t, y0 + w - t)  +\
                self.__auxVertice(x0 + d, z0    , y0 + w)
        return(tmpV1 + tmpV2 + tmpV3 + tmpV4)
    
    def __buildOuterFrame(self):
        # Now that we have all the vertices, we can build the frames:
        
        # Back rim will need to be the same as the back material,
        # or else the rim will be seen on the back (because we are
        # designing the back with zero thickness)
        if not self.back:
            backMtl = self.rimMaterial
        else:
            backMtl = self.exteriorMaterial if self.back["backMaterial"] is None else self.back["backMaterial"]
        Bottom = "g Bottom board\n" \
          + self.__auxMtlName(self.rimMaterial) + "f 8 15 16 5\n"  \
          + self.__auxMtlName(backMtl) + "f 13 14 4 1\n" \
          + self.__auxMtlName(self.exteriorMaterial) + "f 5 16 13 1\n" \
          + self.__auxMtlName(self.interiorMaterial) + "f 14 15 8 4\n"

        if self.openTop:
            Top = ""
            Top = self.__auxMtlName(self.rimMaterial) + "f 7 6 2 3\nf 9 10 11 12\n"
            # TODO - desenhar as orlas no topo
        else:
            Top = "g Top board\n" \
              + self.__auxMtlName(self.rimMaterial) + "f 11 12 7 6\n" \
              + self.__auxMtlName(backMtl) + "f 9 10 2 3\n" \
              + self.__auxMtlName(self.exteriorMaterial) + "f 10 11 6 2\n" \
              + self.__auxMtlName(self.interiorMaterial) + "f 7 12 9 3\n"
                
        Left = "g Left board\n" \
          + self.__auxMtlName(self.rimMaterial) + "f 5 6 7 8\n" \
          + self.__auxMtlName(backMtl) + "f 4 3 2 1\n" \
          + self.__auxMtlName(self.exteriorMaterial) + "f 6 5 1 2\n" \
          + self.__auxMtlName(self.interiorMaterial) + "f 8 7 3 4\n"

        Right = "g Right board\n" \
          + self.__auxMtlName(self.rimMaterial) + "f 12 11 16 15\n" \
          + self.__auxMtlName(backMtl) + "f 14 13 10 9\n" \
          + self.__auxMtlName(self.exteriorMaterial) + "f 13 16 11 10\n" \
          + self.__auxMtlName(self.interiorMaterial) + "f 9 12 15 14\n"

        return(Bottom + Top + Left + Right)

    def __buildBack(self):
        if not self.back: return("") # if back is not defined, there is nothing to do here...
        frontMtl = self.interiorMaterial if self.back["frontMaterial"] is None else self.back["frontMaterial"]
        backMtl = self.exteriorMaterial if self.back["backMaterial"] is None else self.back["backMaterial"]
        # for simplicity reasons, both front and back will be based on
        # existing vertices, so the thickness of the back will be zero
        back = "g Back\n" +\
          self.__auxMtlName(backMtl) + "f 13 10 2 1\n" +\
          self.__auxMtlName(frontMtl) + "f 1 2 10 13\n"
        return(back)
        
    def __buildFronts(self):
        # We use alternate variables for code clarity
        z0 = self.z0
        d = self.depth
        b1 = self.width
        b2 = self.thickness
        result = ""
        for f in self.fronts:
            sc = 0 if f["sizeCorrection"] is None else f["sizeCorrection"]
            x = self.x0 + self.depth
            y = self.y0 + sc + (0 if f["y"] is None else f["y"])
            z = self.z0 + sc + (0 if f["z"] is None else f["z"])
            w = (self.width if f["width"] is None else f["width"]) - 2*sc
            h = (self.height if f["height"] is None else f["height"]) -2*sc
            t = self.thickness
            frtMtl = self.frontMaterial if f["frontMaterial"] is None else f["frontMaterial"]

            result += "\ng %s\n" %(f["frontName"])
            result += self.__auxVertice(x, z  , y)   # -8
            result += self.__auxVertice(x, z+h, y)   # -7
            result += self.__auxVertice(x, z+h, y+w) # -6
            result += self.__auxVertice(x, z  , y+w) # -5
            result += self.__auxMtlName(self.interiorMaterial) + "f -1 -2 -3 -4\n"

            result += self.__auxVertice(x+t, z  , y)   # -4
            result += self.__auxVertice(x+t, z+h, y)   # -3
            result += self.__auxVertice(x+t, z+h, y+w) # -2
            result += self.__auxVertice(x+t, z  , y+w) # -1
            result += self.__auxMtlName(frtMtl) + "f -4 -3 -2 -1\n"

            result += self.__auxMtlName(frtMtl) + "f -8 -7 -3 -4\n"
            result += self.__auxMtlName(frtMtl) + "f -7 -6 -2 -3\n"
            result += self.__auxMtlName(frtMtl) + "f -6 -5 -1 -2\n"
            result += self.__auxMtlName(frtMtl) + "f -5 -8 -4 -2\n"

        return(result)
            
    def __buildShelves(self):
        # We use alternate variables for code clarity
        x0 = self.x0
        y0 = self.y0
        z0 = self.z0
        b1 = self.width
        result = ""
        for s in self.shelves:
            z1 = s["z1"]
            z2 = z1 if s["z2"] is None else s["z2"]
            t = self.thickness # Thickness of outer frame
            b2 = t if s["thickness"] is None else s["thickness"]
            sd = self.depth if s["startDepth"] is None else s["startDepth"]
            ed = 0 if s["endDepth"] is None else s["endDepth"]
            factor = b2/b1
            slvMtl = self.shelveMaterial if s["shelveMaterial"] is None else s["shelveMaterial"]
            rimMtl = self.rimMaterial if s["rimMaterial"] is None else s["rimMaterial"]
            # Back rim will need to be the same as the back material,
            # or else the rim will be seen on the back (because we are
            # designing the back with zero thickness)
            if not self.back:
                backMtl = rimMtl
            else:
                backMtl = self.exteriorMaterial if self.back["backMaterial"] is None else self.back["backMaterial"]
            a1 = z1-z2
            a2 = a1 * factor
            c2 = math.sqrt(b2**2+a2**2)
            result += "\ng %s\n" %(s["shelveName"])
            result += self.__auxVertice(x0 + ed, z0 + z2     , y0 + t)
            result += self.__auxVertice(x0 + ed, z0 + z1     , y0 + b1 - t)
            result += self.__auxVertice(x0 + sd, z0 + z1     , y0 + b1 - t)
            result += self.__auxVertice(x0 + sd, z0 + z2     , y0 + t)
            result += self.__auxVertice(x0 + ed, z0 + z2 + c2, y0 + t)
            result += self.__auxVertice(x0 + ed, z0 + z1 + c2, y0 + b1 - t)
            result += self.__auxVertice(x0 + sd, z0 + z1 + c2, y0 + b1 - t)
            result += self.__auxVertice(x0 + sd, z0 + z2 + c2, y0 + t)
            result += self.__auxMtlName(slvMtl) + "f -5 -6 -7 -8\nf -4 -3 -2 -1\n"
            result += self.__auxMtlName(rimMtl) + "f -6 -5 -1 -2\n"
            result += self.__auxMtlName(backMtl) + "f -8 -7 -3 -4\n"
            ## TODO: calcular os ângulos das prateleiras e colocar no comentário
        return(result)

    def __buildObject(self):
        vertices = self.__buildOuterVertices()
        outerFrame = self.__buildOuterFrame()
        back = self.__buildBack()
        shelves = self.__buildShelves()
        fronts = self.__buildFronts()
        return(vertices + outerFrame + back + shelves + fronts)

    def getObjDefenition(self):
        if self.materialsFileName is None:
            mtlFileName = self.objectName + ".mtl"
        else:
            mtlFileName = self.materialsFileName

        objData = ("mtllib " + mtlFileName + "\n\n")
        objData += self.__buildObject()
        return(objData)

    def saveObjFiles(self):
        objFileName = self.objectName + ".obj"
        objData = "# Object file " + objFileName + "\n\n"
        objData += self.getObjDefenition()

        try:
            with open(objFileName, "x") as objFile:
                objFile.write(objData)
        except Exception as err:
            print(f"Error {err=}, {type(err)=} while opening {objFileName=}")
            return(False)
        
        return(True)


x1 = furniture("WineStand", 35, 35, 180, exteriorMaterial="Exterior", rimMaterial="Rim"\
                  , materialsFileName='Materials.mtl', interiorMaterial="Interior"\
                  , shelveMaterial="Shelve", frontMaterial="Front")

x1.addBack(backMaterial="BackExt", frontMaterial="BackInt")
x1.addShelve(41.5, 1.5)
x1.addShelve(1.5, 50)
x1.addShelve(43.63, 60)
x1.addShelve(50, 105)
x1.addShelve(80, 61.63)
x1.addShelve(100, 80)
x1.addShelve(101.7, 127)
x1.addShelve(130, 107.7)
x1.addShelve(131.6, 140)
x1.addShelve(160, 141.7)
x1.addShelve(140, 177)
x1.addShelve(170, 155)
#x1.saveObjFiles()

#####################

x2 = furniture("KitchenBaseCabinet5Drawer", 60, 60, 70, z0=10\
                   , materialsFileName='Materials.mtl', rimMaterial="Rim"\
                   , exteriorMaterial="Exterior", interiorMaterial="Interior"\
                   , shelveMaterial="Shelve", frontMaterial="Front", openTop=True)

x2.addBack(backMaterial="BackExt", frontMaterial="BackInt")
x2.addShelve(z1=12, endDepth=58, thickness=4, shelveMaterial="Rim")
x2.addFront(height=13, sizeCorrection=0.2)

x2.addShelve(z1=27, endDepth=58, thickness=4, shelveMaterial="Rim")
x2.addFront(z=15, height=13, sizeCorrection=0.2)

x2.addShelve(z1=42, endDepth=58, thickness=4, shelveMaterial="Rim")
x2.addFront(z=30, height=13, sizeCorrection=0.2)

x2.addShelve(z1=57, endDepth=58, thickness=4, shelveMaterial="Rim")
x2.addFront(z=45, height=13, sizeCorrection=0.2)

x2.addShelve(z1=67, endDepth=58, thickness=3, shelveMaterial="Rim")
x2.addFront(z=60, height=8 , sizeCorrection=0.2)
#x2.saveObjFiles()


#####################

x3 = furniture("KitchenBaseCabinet", 60, 60, 70, z0=10, materialsFileName='Materials.mtl'\
                   , rimMaterial="Rim", exteriorMaterial="Exterior"\
                   , interiorMaterial="Interior", shelveMaterial="Shelve"\
                   , frontMaterial="Front", openTop=True)

x3.addBack(backMaterial="BackExt", frontMaterial="BackInt")

x3.addShelve(z1=67, endDepth=58, thickness=3, shelveMaterial="Rim")
x3.addFront(height=68 , sizeCorrection=0.2)
#x3.saveObjFiles()


#####################

x4 = furniture("KitchenTallCabinet", 55, 35, 210, z0=10, materialsFileName='Materials.mtl'\
                  , rimMaterial="Rim", exteriorMaterial="Exterior"\
                  , interiorMaterial="Interior", shelveMaterial="Shelve"\
                  , frontMaterial="Front")

x4.addBack(backMaterial="BackExt", frontMaterial="BackInt")
x4.addFront(sizeCorrection=0.2)
#x4.saveObjFiles()


#####################

x5 = furniture("KitchenOpenCabinet3Shelves", 40, 40, 70, z0=10, materialsFileName='Materials.mtl'\
                  , rimMaterial="Rim", exteriorMaterial="Exterior"\
                  , interiorMaterial="Interior", shelveMaterial="Shelve"\
                  , frontMaterial="Front")

x5.addBack(backMaterial="BackExt", frontMaterial="BackInt")
x5.addShelve(22)
x5.addShelve(45)
#x5.saveObjFiles()

#####################

x6 = furniture("KitchenOpenCabinet2Shelves", 60, 40, 70, z0=10, materialsFileName='Materials.mtl'\
                  , rimMaterial="Rim", exteriorMaterial="Exterior"\
                  , interiorMaterial="Interior", shelveMaterial="Shelve"\
                  , frontMaterial="Front")

x6.addBack(backMaterial="BackExt", frontMaterial="BackInt")
x6.addShelve(33)
#x6.saveObjFiles()


#####################

x7 = furniture("KitchenOpenCabinet4Shelves", 17, 40, 70, z0=10, materialsFileName='Materials.mtl'\
                  , rimMaterial="Rim", exteriorMaterial="Exterior"\
                  , interiorMaterial="Interior", shelveMaterial="Shelve"\
                  , frontMaterial="Front")

x7.addBack(backMaterial="BackExt", frontMaterial="BackInt")
x7.addShelve(1*17.5)
x7.addShelve(2*17.5)
x7.addShelve(3*17.5)
#x7.saveObjFiles()

zz={"test":{"z":1, "location":{"x0":0, "y0":0, "z0":0}}}

with open('x.yaml', 'w') as yaml_file:
    yaml.dump(zz, yaml_file)

#    yaml.dump(x1, yaml_file)
#    yaml.dump(x2, yaml_file)
#    yaml.dump(x3, yaml_file)
#    yaml.dump(x4, yaml_file)
#    yaml.dump(x5, yaml_file)
#    yaml.dump(x6, yaml_file)
#    yaml.dump(x7, yaml_file)

