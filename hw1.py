import requests
import matplotlib.pyplot as plt

def get_list_by_repo(repo, name_organization):
    list_commit = []
    after = None
    while True:
        part_of_commits = get_part_of_commits(repo, name_organization, after)
        if not part_of_commits[2]:
            break
        list_commit.extend(part_of_commits[0])
        after = part_of_commits[1]
        if len(part_of_commits[0]) != 100:
            break
    return list_commit

def get_part_of_commits(repo, name_organization, after):
    if after is None:
        query = '''
            query($name: String!, $owner: String!) {
                repository(name: $name, owner: $owner) {
                    defaultBranchRef {
                        target {
                            ... on Commit {
                                history(first: 100) {
                                edges {
                                    node {
                                            author {
                                              email
                                            }
                                            parents{
                                                totalCount
                                                }
                                          }
                                    }
                                pageInfo {
                                    endCursor
                                    }
                                }
                            }
                        }
                    }
                }
            }
            '''
        data = {
            'query': query,
            'variables': {"owner": name_organization, "name": repo['name']}
        }
    else:
        query = '''
                query($name: String!, $owner: String!, $after: String!) {
                    repository(name: $name, owner: $owner) {
                        defaultBranchRef {
                            target {
                                ... on Commit {
                                    history(first: 100, after: $after) {
                                        edges {
                                            node {
                                                    author {
                                                      email
                                                    }
                                                    parents{
                                                        totalCount
                                                    }
                                                  }
                                            }
                                        pageInfo {
                                            endCursor
                                            }
                                    }
                                }
                            }
                        }
                    }
                }
                '''
        data = {
            'query': query,
            'variables': {"owner": name_organization, "name": repo['name'], 'after': after},
        }

    url = 'https://api.github.com/graphql'

    response = requests.post(url, json=data, headers=headers)
    data = response.json()
    if data['data']['repository']['defaultBranchRef'] is None:
        return [], None, False

    commits = data['data']['repository']['defaultBranchRef']['target']['history']['edges']
    new_after = data['data']['repository']['defaultBranchRef']['target']['history']['pageInfo']['endCursor']
    return commits, new_after, True

def get_list_repo(name_organization):
    repos = []
    url = f"https://api.github.com/users/{name_organization}/repos"
    params = {"per_page": 1000000, "page": 1}

    while True:
        response = requests.get(url, params=params, headers=headers)
        if not response.ok:
            break
        repo_list = response.json()
        if not repo_list:
            break

        repos.extend(repo_list)
        params["page"] += 1
    return repos

def parse_commits(commits):
    for node in commits:
        commit = node['node']
        add_commit_in_dict(commit, dict_amount_commits_by_email)

def add_commit_in_dict(commit, dictionary):
    if commit['parents']['totalCount'] != 1:
        return
    email = commit['author']['email']
    if email == None:
        return
    if email in dictionary:
        dictionary[email] += 1
    else:
        dictionary[email] = 1

def parse_repos_in_dict(list_repo):
    i=0
    for repo in list_repo:
        commits = get_list_by_repo(repo, name_organization)
        parse_commits(commits)
        i+=1
        print(i)

def get_points(d : dict):
    max_v = max(d.values())
    x = [i for i in range(1, max_v + 1)]
    y = [0] * max_v
    for value in d.values():
        y[value-1] += 1
    return (x, y)



if __name__=="__main__":
    token = "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"
    headers = {"Authorization": f"Bearer {token}"}
    dict_amount_commits_by_email = {}

    name_organization = "Yandex"

    list_repo = get_list_repo(name_organization)
    parse_repos_in_dict(list_repo)
    sorted_list_authors = sorted(dict_amount_commits_by_email.items(), key=lambda item: item[1], reverse=True)
    points = get_points(dict_amount_commits_by_email)
    plt.grid()
    plt.bar(points[0], points[1], color='r', linestyle='-')
    plt.xlabel("Кол-во коммитов")
    plt.ylabel("Кол-во людей, вливших столько коммитов")
    plt.title("Диаграмма распределения коммитов между людьми")
    plt.show()
    print(sorted_list_authors[0][0])