import cli

class CreateTestData(cli.CkanCommand):
    '''Create test data in the database.

    create-test-data         - annakarenina and warandpeace
    create-test-data search  - realistic data to test search
    create-test-data gov     - government style data
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 0
    author = u'tester'
    
    def command(self):
        self._load_config()
        self._setup_app()
        if self.args:
            cmd = self.args[0]
        else:
            cmd = 'basic'
        if self.verbose:
            print 'Creating %s test data' % cmd
        if cmd == 'basic':
            self.create_basic_test_data()
        elif cmd == 'search':
            self.create_search_test_data()
        elif cmd == 'gov':
            self.create_gov_test_data(gov_items)
        else:
            print 'Command %s not recognized' % cmd
            raise NotImplementedError
        if self.verbose:
            print 'Creating %s test data: Complete!' % cmd

    @classmethod
    def create_basic_test_data(self):
        self.create()

    @classmethod
    def create_search_test_data(self):
        self.create_arbitrary(search_items)

    @classmethod
    def create_gov_test_data(self, extra_users=[]):
        self.create_arbitrary(gov_items, extra_user_names=extra_users)

    @classmethod
    def create_arbitrary(self, package_dicts, extra_user_names=[]):
        import ckan.model as model
        model.Session.remove()
        rev = model.repo.new_revision() 
        rev.author = self.author
        rev.message = u'Creating search test data.'
        self.pkg_names = []
        self.tag_names = []
        self.group_names = []
        self.user_names = extra_user_names
        admins_list = [] # list of (package_name, admin_names)
        if isinstance(package_dicts, dict):
            package_dicts = [package_dicts]
        for item in package_dicts:
            pkg = model.Package(name=unicode(item['name']))
            for attr, val in item.items():
                if isinstance(val, str):
                    val = unicode(val)
                if attr=='name':
                    continue                
                if attr in ['title', 'version', 'url', 'notes',
                            'author', 'author_email',
                            'maintainer', 'maintainer_email',
                            ]:
                    setattr(pkg, attr, unicode(val))
                elif attr == 'download_url':
                    pkg.add_resource(unicode(val))
                elif attr == 'resources':
                    for res_dict in val:
                        pkg.add_resource(
                            url=unicode(res_dict['url']),
                            format=unicode(res_dict.get('format')),
                            description=unicode(res_dict.get('description')),
                            hash=unicode(res_dict.get('hash')),
                            )
                elif attr == 'tags':
                    if isinstance(val, (str, unicode)):
                        tags = val.split()
                    elif isinstance(val, list):
                        tags = val
                    else:
                        raise NotImplementedError
                    for tag_name in tags:
                        tag_name = unicode(tag_name)
                        tag = model.Tag.by_name(tag_name)
                        if not tag:
                            tag = model.Tag(name=tag_name)
                            self.tag_names.append(tag_name)
                        pkg.tags.append(tag)
                elif attr == 'groups':
                    for group_name in val.split():
                        group = model.Group.by_name(group_name)
                        if not group:
                            group = model.Group(name=group_name)
                            self.group_names.append(group_name)
                        pkg.groups.append(group)
                elif attr == 'license':
                    license = model.License.by_name(val)
                    pkg.license = license
                elif attr == 'license_id':
                    license = model.License.query.get(val)
                    pkg.license = license
                elif attr == 'extras':
                    pkg.extras = val
                elif attr == 'admins':
                    assert isinstance(val, list)
                    admins_list.append((item['name'], val))
                    for user in val:
                        if user not in self.user_names:
                            self.user_names.append(user)
                else:
                    raise NotImplementedError(attr)
            self.pkg_names.append(item['name'])
            model.setup_default_user_roles(pkg)
            rev = model.repo.new_revision() 
            rev.author = self.author
            rev.message = u'Creating search test data.'
        for user_name in self.user_names:
            model.User(name=unicode(user_name))
        model.repo.commit_and_remove()

        if admins_list:
            for pkg_name, admins in admins_list:
                pkg = model.Package.by_name(unicode(pkg_name))
                admins = [model.User.by_name(unicode(user_name)) for user_name in self.user_names]
                model.setup_default_user_roles(pkg, admins)
            model.repo.commit_and_remove()

    
    @classmethod
    def create(self):
        import ckan.model as model
        model.Session.remove()
        rev = model.repo.new_revision() 
        # same name as user we create below
        rev.author = self.author
        rev.message = u'''Creating test data.
 * Package: annakarenina
 * Package: warandpeace
 * Associated tags, etc etc
'''
        self.pkg_names = [u'annakarenina', u'warandpeace']
        pkg1 = model.Package(name=self.pkg_names[0])
        pkg1.title = u'A Novel By Tolstoy'
        pkg1.version = u'0.7a'
        pkg1.url = u'http://www.annakarenina.com'
        # put an & in the url string to test escaping
        pkg1.resources.append(
            model.PackageResource(
              url=u'http://www.annakarenina.com/download/x=1&y=2',
              format=u'plain text',
              description=u'Full text',
              hash=u'abc123',
              )
            )
        pkg1.resources.append(
            model.PackageResource(
              url=u'http://www.annakarenina.com/index.json',
              format=u'json',
              description=u'Index of the novel',
              hash=u'def456',
              )
            )
        pkg1.notes = u'''Some test notes

### A 3rd level heading

**Some bolded text.**

*Some italicized text.*

Foreign characters:
u with umlaut \xc3\xbc

Needs escaping:
left arrow <

<http://ckan.net/>

'''
        pkg2 = model.Package(name=self.pkg_names[1])
        tag1 = model.Tag(name=u'russian')
        tag2 = model.Tag(name=u'tolstoy')
        pkg1.tags = [tag1, tag2]
        pkg2.tags = [ tag1 ]
        self.tag_names = [u'russian', u'tolstoy']
        license1 = model.License.by_name(u'OKD Compliant::Other')
        pkg1.license = license1
        pkg2.title = u'A Wonderful Story'
        pkg1._extras = {'genre':model.PackageExtra(key=u'genre', value='romantic novel'),
                        'original media':model.PackageExtra(key=u'original media', value='book')
                        }
        # api key
        model.User(name=u'tester', apikey=u'tester')
        self.user_names = [u'tester']
        # group
        david = model.Group(name=u'david',
                             title=u'Dave\'s books',
                             description=u'These are books that David likes.')
        roger = model.Group(name=u'roger',
                             title=u'Roger\'s books',
                             description=u'Roger likes these books.')
        self.group_names = (u'david', u'roger')
        david.packages = [pkg1, pkg2]
        roger.packages = [pkg1]
        # authz
        joeadmin = model.User(name=u'joeadmin')
        annafan = model.User(name=u'annafan', about=u'I love reading Annakarenina')
        russianfan = model.User(name=u'russianfan')
        testsysadmin = model.User(name=u'testsysadmin')
        self.user_names.extend([u'joeadmin', u'annafan', u'russianfan', u'testsysadmin'])
        model.repo.commit_and_remove()

        visitor = model.User.by_name(model.PSEUDO_USER__VISITOR)
        anna = model.Package.by_name(u'annakarenina')
        war = model.Package.by_name(u'warandpeace')
        model.setup_default_user_roles(anna, [annafan])
        model.setup_default_user_roles(war, [russianfan])
        model.add_user_to_role(visitor, model.Role.ADMIN, war)
        model.setup_default_user_roles(david, [russianfan])
        model.setup_default_user_roles(roger, [russianfan])
        model.add_user_to_role(visitor, model.Role.ADMIN, roger)

        model.repo.commit_and_remove()


    @classmethod
    def delete(self):
        import ckan.model as model
        for pkg_name in self.pkg_names:
            pkg = model.Package.by_name(unicode(pkg_name))
            if pkg:
                pkg.purge()
        for tag_name in self.tag_names:
            tag = model.Tag.by_name(unicode(tag_name))
            if tag:
                tag.purge()
        revs = model.Revision.query.filter_by(author=self.author)
        for rev in revs:
            model.Session.delete(rev)
        for group_name in self.group_names:
            group = model.Group.by_name(unicode(group_name))
            if group:
                model.Session.delete(group)
        for user_name in self.user_names:
            user = model.User.by_name(unicode(user_name))
            if user:
                user.purge()
        model.Session.commit()
        model.Session.remove()


search_items = [{'name':'gils',
              'title':'Government Information Locator Service',
              'url':'',
              'tags':'registry  country-usa  government  federal  gov  workshop-20081101',
              'groups':'ukgov test1 test2 penguin',
              'license':'OKD Compliant::Other',
              'notes':'''From <http://www.gpoaccess.gov/gils/about.html>
              
> The Government Information Locator Service (GILS) is an effort to identify, locate, and describe publicly available Federal
> Because this collection is decentralized, the GPO''',
              'extras':{'date_released':'2008'},
              },
             {'name':'us-gov-images',
              'title':'U.S. Government Photos and Graphics',
              'url':'http://www.usa.gov/Topics/Graphics.shtml',
              'download_url':'http://www.usa.gov/Topics/Graphics.shtml',
              'tags':'images  graphics  photographs  photos  pictures  us  usa  america  history  wildlife  nature  war  military  todo-split  gov',
              'groups':'ukgov test1 penguin',
              'license':'OKD Compliant::Other',
              'notes':'''## About

Collection of links to different US image collections in the public domain.

## Openness

> Most of these images and graphics are available for use in the public domain, and''',
              'extras':{'date_released':'2009'},
              },
             {'name':'usa-courts-gov',
              'title':'Text of US Federal Cases',
              'url':'http://bulk.resource.org/courts.gov/',
              'download_url':'http://bulk.resource.org/courts.gov/',
              'tags':'us  courts  case-law  us  courts  case-law  gov  legal  law  access-bulk  penguins penguin',
              'groups':'ukgov test2 penguin',
              'license':'OKD Compliant::Creative Commons CCZero',
              'notes':'''### Description

1.8 million pages of U.S. case law available with no restrictions. From the [README](http://bulk.resource.org/courts.gov/0_README.html):

> This file is  http://bulk.resource.org/courts.gov/0_README.html and was last revised''',
              'extras':{'date_released':'2007-06'},
              },
             {'name':'uk-government-expenditure',
              'title':'UK Government Expenditure',
              'tags':'workshop-20081101  uk  gov  expenditure  finance  public  funding',
              'groups':'ukgov penguin',              
              'notes':'''Discussed at [Workshop on Public Information, 2008-11-02](http://okfn.org/wiki/PublicInformation).

Overview is available in Red Book, or Financial Statement and Budget Report (FSBR), [published by the Treasury](http://www.hm-treasury.gov.uk/budget.htm).''',
              'extras':{'date_released':'2007-10'},
              },
             {'name':'se-publications',
              'title':'Sweden - Government Offices of Sweden - Publications',
              'url':'http://www.sweden.gov.se/sb/d/574',
              'groups':'penguin',              
              'tags':'country-sweden  format-pdf  access-www  documents  publications  government  eutransparency',
              'license':'Other::License Not Specified',
              'notes':'''### About

Official documents including "government bills and reports, information material and other publications".

### Reuse

Not clear.''',
              'extras':{'date_released':'2009-10-27'},
              },
             {'name':'se-opengov',
              'title':'Opengov.se',
              'groups':'penguin',              
              'url':'http://www.opengov.se/',
              'download_url':'http://www.opengov.se/data/open/',
              'tags':'country-sweden  government  data',
              'license':'OKD Compliant::Creative Commons Attribution-ShareAlike',
              'notes':'''### About

From [website](http://www.opengov.se/sidor/english/):

> Opengov.se is an initiative to highlight available public datasets in Sweden. It contains a commentable catalog of government datasets, their formats and usage restrictions.

> The goal is to highlight the benefits of open access to government data and explain how this is done in practice.

### Openness

It appears that the website is under a CC-BY-SA license. Legal status of the data varies. Data that is fully open can be viewed at:

 * <http://www.opengov.se/data/open/>'''
              },
             ]


gov_items = [
    {'name':'private-fostering-england-2009',
     'title':'Private Fostering',
     'notes':'Figures on children cared for and accommodated in private fostering arrangements, England, Year ending 31 March 2009',
     'resources':[{'url':'http://www.dcsf.gov.uk/rsgateway/DB/SFR/s000859/SFR17_2009_tables.xls',
                  'format':'XLS',
                  'description':''}],
     'url':'http://www.dcsf.gov.uk/rsgateway/DB/SFR/s000859/index.shtml',
     'author':'DCSF Data Services Group',
     'author_email':'statistics@dcsf.gsi.gov.uk',
     'license':'Non-OKD Compliant::Crown Copyright',
     'tags':'children fostering',
     'extras':{
        'external_reference':'DCSF-DCSF-0024',
        'date_released':'2009-07-30',
        'date_updated':'2009-07-30',
        'update_frequency':'annually',
        'geographic_granularity':'regional',
        'geographic_coverage':'100000: England',
        'department':'Department for Children, Schools and Families',
        'temporal_granularity':'years',
        'temporal_coverage-from':'2008-6',
        'temporal_coverage-to':'2009-6',
        'categories':'Health, well-being and Care',
        'national_statistic':'yes',
        'precision':'Numbers to nearest 10, percentage to nearest whole number',
        'taxonomy_url':'',
        'agency':'',
        }
     },
    {'name':'weekly-fuel-prices',
     'title':'Weekly fuel prices',
     'notes':'Latest price as at start of week of unleaded petrol and diesel.',
     'resources':[{'url':'', 'format':'XLS', 'description':''}],
     'url':'http://www.decc.gov.uk/en/content/cms/statistics/source/prices/prices.aspx',
     'author':'DECC Energy Statistics Team',
     'author_email':'energy.stats@decc.gsi.gov.uk',
     'license':'Non-OKD Compliant::Crown Copyright',
     'tags':'fuel prices',
     'extras':{
        'external_reference':'DECC-DECC-0001',
        'date_released':'2009-11-24',
        'date_updated':'2009-11-24',
        'update_frequency':'weekly',
        'geographic_granularity':'national',
        'geographic_coverage':'111100: United Kingdom (England, Scotland, Wales, Northern Ireland)',
        'department':'Department of Energy and Climate Change',
        'temporal_granularity':'weeks',
        'temporal_coverage-from':'2008-11-24',
        'temporal_coverage-to':'2009-11-24',
        'national_statistic':'yes',
        }
     }
    ]
