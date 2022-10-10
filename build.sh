# we're going to use `git archive` to create the zip file, so we need
# to warn if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "There are uncommitted changes. This build will ONLY INCLUDE COMMITTED CHANGES."
    read -p "Would you like to build anyway (ignoring uncommitted changes)? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Creating zip file for add-on"

# extract the version number from __init.py__
# TODO: There's probably a better way to do this! 
#       I couldn't find a safe, cross-platform way.
version_str=$(grep -E "version" ./__init__.py)
major_version=$(grep -oE '\(\d+' <<< "$version_str")
major_version=$(grep -oE '\d+' <<< "$major_version")
minor_version=$(grep -oE ',\s*\d+,' <<< "$version_str")
minor_version=$(grep -oE '\d+' <<< "$minor_version")
revision_version=$(grep -oE ',\s*\d+\),' <<< "$version_str")
revision_version=$(grep -oE '\d+' <<< "$revision_version")

version_str_for_file="$major_version-$minor_version-$revision_version"
filename="../AI-Render-v$version_str_for_file.zip"

# create a zip file using git, so we can create a top-level directory
# in the zip, and so it ignores all .gitignore patterns
git archive HEAD --prefix=AI-Render/ --format=zip -o ${filename}

echo "Zip file in ${filename}"