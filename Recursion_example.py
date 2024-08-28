aa = ['am', 'am.hello', 'abc.hello.am', 'am.hello.aa.tt', 'am.hello.aa.tt.ags']
bb = ['t01.am.test.box', 't01.am.hello.box', 't01.am.hello.hello.box', 't01.abc.hello.am.tt.box', 't02.am.hello.aa.tt.ags.empty', 't02.am.hello.aa.tt.ags.empty.am']
res = set()

    
def parsestr(s):
    if s in aa:
        res.add(s)
    elif '.' in s:
        b = s.rsplit('.', 1)
        parsestr(b[0])
    else:
        return
        
for i in bb:
    k = i.split('.',1)
    parsestr(k[-1])
print(res)
-------------------------------------------------------
#without recursion

def parsestr(s):
    # Start from the end and keep removing the last segment
    while s:
        if s in aa:
            res.add(s)
            return
        if '.' in s:
            s = s.rsplit('.', 1)[0]
        else:
            break

for i in bb:
    k = i.split('.', 1)[-1]
    parsestr(k)

print(res)
--------------------------------------------------------
#without recursion
import pandas as pd

# Define the lists
aa = ['am', 'am.hello', 'abc.hello.am', 'am.hello.aa.tt', 'am.hello.aa.tt.ags']
bb = ['t01.am.test.box', 't01.am.hello.box', 't01.am.hello.hello.box', 't01.abc.hello.am.tt.box', 't02.am.hello.aa.tt.ags.empty', 't02.am.hello.aa.tt.ags.empty.am']

# Convert aa to a set for O(1) lookup
aa_set = set(aa)

# Convert bb to a DataFrame
df_bb = pd.DataFrame(bb, columns=['Path'])

# Initialize lists to store results
prefixes = []
full_strings = []
matches = []

# Process each row in the DataFrame
for item in df_bb['Path']:
    # Extract prefix and full string
    prefix = item.split('.', 1)[0]
    suffix = item  # Start with the full item as suffix
    
    # Check for matches
    matched = []
    while suffix:
        if suffix in aa_set:
            matched.append(suffix)
            
        if '.' in suffix:
            suffix = suffix.rsplit('.', 1)[0]
        else:
            break
    
    # Append results to lists
    prefixes.append(prefix)
    full_strings.append(item)
    matches.append(matched if matched else None)  # Append None if no matches found

# Create the output DataFrame
output_df = pd.DataFrame({
    'prefix': prefixes,
    'item': full_strings,
    'matched': matches
})

print(output_df)
--------------------------------------------------------
Is all db_name available in autosys_instance csv file are always available in db.csv file
If yes then is db.csv will always have server-> no then from where server info present of instance db_name
Is it possible db.csv can have autosys_instance server
If yes means there is relation between db and job also 
Means job has target_machine (virtual/host) which has underneath host and that host can be db_server or instance or actual_server
If no means then how jobconfig is related to database
Is there any direct relation between jobmask and database  - hopefully no
But i want to know database by jobmask then host is the intermediate
Is it possible for you to give instance in db.csv 



